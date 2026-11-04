"""Fluxo pedagógico de um turno.

  1. Valida a entrada e carrega a memória da sessão.
  2. Classifica a intenção (fluxo_heuristico) e registra o nível declarado.
  3. Barreiras determinísticas: saudação, padrão inventado ou inexistente,
     outro padrão, solução pronta e fora de escopo são respondidos sem o modelo.
  4. Monta o plano do turno: agentes autores, contexto, nível e material
     verificado (código Java compilado, diagrama UML).
  5. Executa a crew: autores (com guardrails) e o Guardião (veredito).
  6. Só entrega texto aprovado. Uma reprovação fundamentada permite uma
     rodada de correção seguida de nova revisão; incerteza ou erro persistente
     produzem orientação segura sem expor o rascunho. Exceção: na avaliação de
     uma tentativa, o Guardião não tem o gabarito; ali um INCONCLUSIVO não
     bloqueia, e a validação automática (que confere se o gabarito não foi
     revelado) decide.
  7. Monta a resposta final (material verificado + texto dos agentes) e salva
     o turno na memória.
"""

from __future__ import annotations

import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field

from . import recusas
from .avaliacao_exercicio import AVALIADORES
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
from .crew import (
    INTENCOES_AVALIACAO, INTENCOES_COM_PERGUNTA, PlanoTurno, montar_crew, montar_crew_reescrita, montar_crew_revisao,
    pergunta_final_padrao, referencia_revisao, problemas_textos,
)
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
    avaliar_revisao,
    garantir_pergunta_final,
    premissas_falsas,
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
            intencao.tipo in INTENCOES_AVALIACAO or "exerc" in p
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
    if "inquiridor" in agentes and intencao.tipo in INTENCOES_AVALIACAO:
        exercicio = exercicio_por_id(memoria.exercicio_atual)
        if exercicio:
            plano.gabarito = exercicio.gabarito
            plano.enunciado = exercicio.enunciado
        falas, respostas = [], []
        for turno in reversed(memoria.historico):
            if turno.get("intencao") == "exercicio":
                break
            falas.append(turno.get("pergunta", ""))
            if turno.get("tipo") == "resposta":
                respostas.append(turno.get("resposta", ""))
        falas.reverse()
        respostas.reverse()
        plano.fala_estudante = "\n".join([*falas, pergunta])
        plano.respostas_anteriores = respostas
        if exercicio:
            plano.contexto = _contexto_avaliacao(exercicio, falas, respostas)
            avaliador = AVALIADORES.get(exercicio.ident)
            if avaliador:
                # Avaliação verificada (sem modelo): o Inquiridor só redige o retorno.
                plano.avaliacao = avaliador(plano.fala_estudante)
                plano.fatos["inquiridor"] = plano.avaliacao.fatos()
    return plano, exemplo


def _contexto_avaliacao(exercicio, falas: list[str], respostas: list[str]) -> str:
    """Estado do exercício para o Inquiridor, sem as respostas anteriores do
    sistema (o modelo de 3B copiava a última). Só a última pergunta feita entra."""
    partes = [f"Enunciado do exercício em andamento:\n{exercicio.enunciado}"]
    if falas:
        partes.append("Tentativas anteriores do estudante neste exercício (dados):\n"
                      + "\n".join(f"- {f}" for f in falas))
    if respostas:
        ultima = [f for f in re.split(r"(?<=[.!?])\s+", respostas[-1].strip()) if f.endswith("?")]
        if ultima:
            partes.append(f"Última pergunta feita ao estudante: {ultima[-1]}")
    return "\n\n".join(partes)


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
        elif autor == "inquiridor" and plano.avaliacao is not None and plano.intencao == "avaliacao":
            # A pergunta seguinte é a verificada; as do modelo saem.
            frases = re.split(r"(?<=[.!?])\s+", texto)
            blocos.append(" ".join(f for f in frases if not f.rstrip().endswith("?")).strip())
            pergunta_final = plano.avaliacao.pergunta
        elif autor == "tutor" and plano.intencao == "conceito" and plano.pergunta_geral:
            corpo, pergunta_final = _separar_pergunta_final(texto)
            blocos += [corpo, "```text\n" + carregar_uml() + "\n```"]
        else:
            blocos.append(texto)
            pergunta_final = ""
    if pergunta_final:
        blocos.append(pergunta_final)
    resposta = "\n\n".join(b for b in blocos if b)
    if plano.intencao not in INTENCOES_COM_PERGUNTA:
        return resposta
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

    if intencao.tipo == "exercicio" or intencao.tipo in INTENCOES_SEM_MODELO:
        extras = {}
        if intencao.tipo == "exercicio":
            exercicio = escolher_exercicio(memoria.exercicios_propostos)
            resposta, agente = exercicio.enunciado, "inquiridor"
            extras["exercicio"] = exercicio.ident
        else:
            resposta = _resposta_deterministica(intencao, memoria)
            agente = "regra_deterministica"
        memoria.salvar_turno(
            pergunta, resposta, agente, intencao=intencao.tipo,
            tipo="orientacao", nivel=nivel, **extras,
        )
        return ResultadoFluxo(
            resposta=resposta, agente_ultimo=agente, sessoes_atualizadas=True,
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
    # As saídas já passaram pelo guardrail. Não modificar texto após a revisão.
    textos = {autor: str(t.raw or "") for autor, t in zip(plano.agentes, saidas_tarefas[:-1])}
    decisao = avaliar_revisao(str(saidas_tarefas[-1].raw or ""), textos,
                             pergunta, referencia_revisao(plano))
    tentativas = [decisao]
    reescrito = False
    falha_correcao = False
    if decisao["veredito"] == "REPROVADO" and MAX_REESCRITAS_GUARDIAO > 0:
        try:
            # Uma rodada: cada autor citado é chamado no máximo uma vez.
            for autor in plano.agentes:
                problemas = [p for p in decisao["problemas"] if p["autor"] == autor]
                if problemas:
                    nova = _executar(lambda: montar_crew_reescrita(plano, autor, textos[autor], problemas))
                    textos[autor] = str(getattr(nova, "raw", "") or "")
                    reescrito = True
            if problemas_textos(plano, textos):
                decisao = {"veredito": "INCONCLUSIVO", "problemas": [],
                           "problemas_descartados": [], "motivo": "Correção falhou na validação automática."}
            else:
                revisada = _executar(lambda: montar_crew_revisao(plano, textos))
                decisao = avaliar_revisao(str(getattr(revisada, "raw", "") or ""), textos,
                                         pergunta, referencia_revisao(plano))
        except (ErroModeloIndisponivel, ErroSaidaInesperada):
            falha_correcao = True
            decisao = {"veredito": "INCONCLUSIVO", "problemas": [],
                       "problemas_descartados": [], "motivo": "Não foi possível concluir a correção/revisão."}
        tentativas.append(decisao)

    problemas_finais = problemas_textos(plano, textos)
    # Teste web de 04/11: as duas avaliações de "o product seria o recibo" foram
    # bloqueadas porque o Guardião inventou críticas (descartadas) e virou
    # INCONCLUSIVO. Na avaliação, sem gabarito, ele não consegue decidir.
    sem_decisao_na_avaliacao = (plano.intencao in INTENCOES_AVALIACAO
                                and decisao["veredito"] == "INCONCLUSIVO" and not falha_correcao)
    bloqueada = ((decisao["veredito"] != "APROVADO" and not sem_decisao_na_avaliacao)
                 or bool(problemas_finais))
    revisao = {**decisao, "reescrito": reescrito, "bloqueada": bloqueada,
               "tentativas": tentativas, "validacao_automatica": problemas_finais,
               "falha_correcao": falha_correcao,
               "entregue_sem_aprovacao": sem_decisao_na_avaliacao and not bloqueada}
    if bloqueada and plano.avaliacao is not None:
        # Em vez de "não consegui validar", o retorno verificado do sistema.
        resposta = plano.avaliacao.texto() + "\n\n" + plano.avaliacao.pergunta
        revisao["resposta_verificada"] = True
    elif bloqueada:
        resposta = recusas.resposta_nao_validada()
    else:
        resposta = _montar_resposta(plano, textos, exemplo)
    tipo = "orientacao" if bloqueada else "resposta"
    agente_ultimo = plano.agentes[-1]
    duracao = round(time.monotonic() - inicio, 2)
    memoria.salvar_turno(
        pergunta=pergunta, resposta=resposta, agente=agente_ultimo, intencao=intencao.tipo,
        agentes=plano.agentes + ["guardiao"], tipo=tipo, revisao=revisao,
        nivel=nivel, exemplo=exemplo if not bloqueada else "", duracao_segundos=duracao,
        # Exercício terminado: a próxima mensagem não é mais tratada como resposta.
        exercicio_concluido=bool(plano.avaliacao is not None and plano.avaliacao.concluido),
    )
    return ResultadoFluxo(
        resposta=resposta, agente_ultimo=agente_ultimo, sessoes_atualizadas=True,
        tipo=tipo, intencao=intencao.tipo, agentes=plano.agentes + ["guardiao"],
        revisao=revisao, duracao_segundos=duracao,
    )
