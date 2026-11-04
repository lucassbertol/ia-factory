"""Fluxo pedagógico de um turno.

  1. Valida a entrada e carrega a memória da sessão.
  2. Classifica a intenção (fluxo_heuristico) e registra o nível declarado.
  3. Barreiras determinísticas: saudação, padrão inventado ou inexistente,
     outro padrão, solução pronta e fora de escopo são respondidos sem o modelo.
  4. Monta o plano do turno: agentes autores, contexto, nível e material
     verificado (código Java compilado, diagrama UML).
  5. Executa a crew: autores (com guardrails) e o Guardião (veredito).
  6. O veredito do Guardião é registrado. A reescrita pedida por ele existe, mas
     vem desligada (MAX_REESCRITAS_GUARDIAO=0): nas três coletas com o modelo
     real ela nunca corrigiu um erro real e piorou 7 respostas.
  7. Monta a resposta final (material verificado + texto dos agentes) e salva
     o turno na memória.
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from . import recusas
from .agentes import TITULOS
from .catalogo import padroes_gof_citados
from .conhecimento import (
    CORRECAO_USO_INCORRETO,
    EXEMPLOS,
    FATOS_EXEMPLOS,
    carregar_uml,
    escolher_exemplo,
    escolher_exercicio,
    exercicio_por_id,
)
from .config import MAX_REESCRITAS_GUARDIAO
from .crew import PlanoTurno, montar_crew, montar_crew_reescrita, pergunta_final_padrao
from .erro import ErroEntradaVazia, ErroModeloIndisponivel, ErroSaidaInesperada
from .fluxo_heuristico import (
    INTENCOES_SEM_MODELO,
    _normaliza,
    classificar_intencao,
    decidir_agentes,
    detectar_nivel,
)
from .memoria import MemoriaConversa
from .verificacao import (
    Exigencias,
    corrigir_mecanicamente,
    cortar_frase_incompleta,
    encontrar_problemas,
    garantir_pergunta_final,
    ler_veredito,
    premissas_falsas,
    problemas_fundamentados,
    remover_meta_revisao,
    remover_repeticoes,
)


@dataclass
class ResultadoFluxo:
    """Resultado de um turno."""

    resposta: str
    agente_ultimo: str
    sessoes_atualizadas: bool
    tipo: str = "resposta"  # "resposta" (modelo) ou "orientacao" (determinística)
    intencao: str = ""
    agentes: list[str] = field(default_factory=list)
    revisao: dict = field(default_factory=dict)
    duracao_segundos: float = 0.0


def _resposta_deterministica(intencao, memoria: MemoriaConversa) -> str:
    tipo = intencao.tipo
    if tipo == "saudacao":
        return recusas.boas_vindas()
    if tipo == "inventicao":
        return recusas.padrao_inventado()
    if tipo == "padrao_desconhecido":
        return recusas.padrao_desconhecido(intencao.detalhe)
    if tipo == "outro_padrao":
        return recusas.outro_padrao(intencao.detalhe)
    if tipo == "solucao_pronta":
        return recusas.solucao_pronta(exercicio_pendente=bool(memoria.exercicio_pendente))
    return recusas.fora_de_escopo()


_PERGUNTA_GERAL = (
    "o que e", "o que eh", "explique o", "explique a ideia", "explica o", "como funciona",
    "qual problema", "que problema", "para que serve", "estrutura", "participantes", "defina",
)


def _planejar(pergunta: str, intencao, memoria: MemoriaConversa, nivel: str) -> tuple[PlanoTurno, str]:
    """Decide agentes, contexto e material verificado. Devolve (plano, exemplo_mostrado)."""
    p = _normaliza(pergunta)
    agentes = [a for a in decidir_agentes(intencao, pergunta) if a != "guardiao"]
    contexto = (
        memoria.contexto_texto(incluir_exercicio=(
            intencao.tipo in {"avaliacao", "esclarecimento"} or "exerc" in p
        ))
        if intencao.usar_contexto else ""
    )
    plano = PlanoTurno(
        pergunta=pergunta,
        intencao=intencao.tipo,
        agentes=agentes,
        contexto=contexto,
        nivel=nivel,
        pergunta_geral=any(t in p for t in _PERGUNTA_GERAL),
        padroes_citados=padroes_gof_citados(p) if intencao.tipo == "comparacao" else [],
        topicos_estudados=memoria.topicos_estudados if intencao.tipo == "fechamento" else [],
        premissas_falsas=premissas_falsas(pergunta),
    )
    exemplo = ""
    if "exemplificador" in agentes:
        if intencao.tipo == "uso_incorreto":
            exemplo = "incorreto"
            plano.material["exemplificador"] = (
                EXEMPLOS["incorreto"].bloco_markdown() + "\n\n" + CORRECAO_USO_INCORRETO
            )
        else:
            exemplo = escolher_exemplo(nivel, memoria.exemplos_mostrados)
            plano.material["exemplificador"] = EXEMPLOS[exemplo].bloco_markdown()
        plano.fatos["exemplificador"] = FATOS_EXEMPLOS[exemplo]
    if "inquiridor" in agentes and intencao.tipo in {"avaliacao", "esclarecimento"}:
        exercicio = exercicio_por_id(memoria.exercicio_atual)
        if exercicio:
            plano.gabarito = exercicio.gabarito
    return plano, exemplo


def _separar_pergunta_final(texto: str) -> tuple[str, str]:
    """Separa o último parágrafo se ele for uma pergunta ao estudante."""
    paragrafos = [p for p in texto.strip().split("\n\n")
                  if not re.fullmatch(r"\s*[#*\s]*pergunta[^\n?]{0,40}[*:\s]*", p, re.IGNORECASE)]
    if len(paragrafos) > 1 and paragrafos[-1].rstrip().endswith("?"):
        return "\n\n".join(paragrafos[:-1]), paragrafos[-1]
    frases = re.split(r"(?<=[.!])\s+", paragrafos[-1].strip())
    if len(frases) > 1 and frases[-1].endswith("?"):
        paragrafos[-1] = " ".join(frases[:-1])
        return "\n\n".join(paragrafos), frases[-1]
    return texto.strip(), ""


def _montar_resposta(plano: PlanoTurno, textos: dict[str, str], exemplo: str) -> str:
    """Intercala o texto dos agentes com o material verificado.

    Quando um material vem depois do texto (diagrama, correção), a pergunta final
    do agente é movida para o fim, para a resposta terminar com ela.
    """
    blocos: list[str] = []
    pergunta_final = ""
    for autor in plano.agentes:
        texto = textos.get(autor, "").strip()
        if autor == "exemplificador" and exemplo == "incorreto":
            corpo, pergunta_final = _separar_pergunta_final(texto)
            blocos += [EXEMPLOS["incorreto"].bloco_markdown(), corpo, CORRECAO_USO_INCORRETO]
        elif autor == "exemplificador" and exemplo:
            blocos += [EXEMPLOS[exemplo].bloco_markdown(), texto]
            pergunta_final = ""
        elif autor == "tutor" and plano.intencao == "conceito" and plano.pergunta_geral:
            corpo, pergunta_final = _separar_pergunta_final(texto)
            blocos += [corpo, "```text\n" + carregar_uml() + "\n```"]
        else:
            blocos.append(texto)
            pergunta_final = ""
    if pergunta_final:
        blocos.append(pergunta_final)
    resposta = "\n\n".join(b for b in blocos if b)
    return garantir_pergunta_final(resposta, pergunta_final_padrao(plano.intencao))


def _causa_ollama(exc: BaseException) -> bool:
    from .llm import FalhaOllama

    atual: BaseException | None = exc
    while atual is not None:
        if isinstance(atual, FalhaOllama):
            return True
        texto = str(atual).lower()
        if "ollama" in texto or "11434" in texto or "connection refused" in texto:
            return True
        atual = atual.__cause__ or atual.__context__
    return False


def _executar(montar):
    """Monta e executa uma crew, convertendo falhas em erros do sistema."""
    try:
        return montar().kickoff()
    except Exception as exc:
        detalhe = str(exc) or type(exc).__name__
        if _causa_ollama(exc):
            raise ErroModeloIndisponivel(detalhe) from exc
        raise ErroSaidaInesperada(detalhe) from exc


def executar_fluxo(
    pergunta: str,
    sessao_id: str = "default",
    *,
    nivel: str = "",
    ao_iniciar: Callable[[list[str]], None] | None = None,
) -> ResultadoFluxo:
    """Executa um turno completo para a pergunta do estudante."""
    inicio = time.monotonic()
    if not pergunta or not pergunta.strip():
        raise ErroEntradaVazia()
    pergunta = pergunta.strip()

    memoria = MemoriaConversa(sessao_id)
    nivel = nivel or detectar_nivel(pergunta) or memoria.nivel
    intencao = classificar_intencao(
        pergunta,
        ultima_intencao=memoria.ultima_intencao,
        exercicio_pendente=bool(memoria.exercicio_pendente),
    )

    # Exercícios vêm de um banco verificado (enunciado + gabarito). Na quarta
    # coleta o modelo inventou um enunciado contraditório que já trazia a solução.
    if intencao.tipo == "exercicio":
        exercicio = escolher_exercicio(memoria.exercicios_propostos)
        memoria.salvar_turno(
            pergunta, exercicio.enunciado, "inquiridor", intencao="exercicio",
            tipo="orientacao", nivel=nivel, exercicio=exercicio.ident,
        )
        return ResultadoFluxo(
            resposta=exercicio.enunciado, agente_ultimo="inquiridor", sessoes_atualizadas=True,
            tipo="orientacao", intencao="exercicio",
            duracao_segundos=round(time.monotonic() - inicio, 2),
        )

    # Barreiras determinísticas (sem chamar o modelo).
    if intencao.tipo in INTENCOES_SEM_MODELO:
        resposta = _resposta_deterministica(intencao, memoria)
        memoria.salvar_turno(
            pergunta, resposta, "regra_deterministica", intencao=intencao.tipo,
            tipo="orientacao", nivel=nivel,
        )
        return ResultadoFluxo(
            resposta=resposta, agente_ultimo="regra_deterministica", sessoes_atualizadas=True,
            tipo="orientacao", intencao=intencao.tipo,
            duracao_segundos=round(time.monotonic() - inicio, 2),
        )

    plano, exemplo = _planejar(pergunta, intencao, memoria, nivel)
    if ao_iniciar:
        ao_iniciar([TITULOS[a] for a in plano.agentes] + [TITULOS["guardiao"]])

    saida = _executar(lambda: montar_crew(plano))
    saidas_tarefas = list(getattr(saida, "tasks_output", []) or [])
    if len(saidas_tarefas) != len(plano.agentes) + 1:
        raise ErroSaidaInesperada(
            f"A crew devolveu {len(saidas_tarefas)} saídas para {len(plano.agentes) + 1} tarefas."
        )
    textos = {
        autor: remover_meta_revisao(str(t.raw or ""))
        for autor, t in zip(plano.agentes, saidas_tarefas[:-1])
    }
    veredito_bruto = str(saidas_tarefas[-1].raw or "")
    aprovado, problemas = ler_veredito(veredito_bruto)
    autor = plano.agentes[-1]
    aceitos, descartados = problemas_fundamentados(problemas, textos[autor])
    revisao = {"veredito": {True: "APROVADO", False: "REPROVADO", None: "ILEGIVEL"}[aprovado],
               "problemas": aceitos, "problemas_descartados": descartados, "reescrito": False}

    # Só reescreve por problemas que citam um trecho real da resposta. A nova
    # versão só substitui a anterior se não tiver mais problemas objetivos.
    if aprovado is False and aceitos and MAX_REESCRITAS_GUARDIAO > 0:
        nova = _executar(lambda: montar_crew_reescrita(plano, autor, textos[autor], aceitos))
        texto_novo = corrigir_mecanicamente(str(getattr(nova, "raw", "") or ""), Exigencias())
        if texto_novo and len(encontrar_problemas(texto_novo, Exigencias())) <= len(
            encontrar_problemas(textos[autor], Exigencias())
        ):
            textos[autor] = texto_novo
            revisao["reescrito"] = True

    textos = {a: cortar_frase_incompleta(remover_repeticoes(t)) for a, t in textos.items()}
    if not any(t.strip() for t in textos.values()):
        raise ErroSaidaInesperada("Os agentes devolveram respostas vazias.")

    resposta = _montar_resposta(plano, textos, exemplo)
    agente_ultimo = plano.agentes[-1]
    duracao = round(time.monotonic() - inicio, 2)
    memoria.salvar_turno(
        pergunta=pergunta, resposta=resposta, agente=agente_ultimo, intencao=intencao.tipo,
        agentes=plano.agentes + ["guardiao"], tipo="resposta", revisao=revisao,
        nivel=nivel, exemplo=exemplo, duracao_segundos=duracao,
    )
    return ResultadoFluxo(
        resposta=resposta, agente_ultimo=agente_ultimo, sessoes_atualizadas=True,
        tipo="resposta", intencao=intencao.tipo, agentes=plano.agentes + ["guardiao"],
        revisao=revisao, duracao_segundos=duracao,
    )
