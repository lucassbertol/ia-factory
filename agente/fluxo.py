"""Fluxo pedagogico do sistema Factory Method.

Orquestra a entrada do estudante, o processamento pelos agentes CrewAI e a
resposta final, integrando memoria, tratamento de erros e revisao do Guardiao.
"""

from __future__ import annotations

from dataclasses import dataclass

from .crew import montar_crew
from .erro import (
    ErroEntradaVazia,
    ErroForaDeEscopo,
    ErroInventicao,
    ErroModeloIndisponivel,
    ErroSaidaInesperada,
    ErroSolucaoPronta,
)
from .fluxo_heuristico import classificar_intencao, decidir_agentes
from .memoria import MemoriaConversa


@dataclass
class ResultadoFluxo:
    """Resultado do processamento do fluxo pedagogico."""

    resposta: str
    agente_ultimo: str
    sessoes_atualizadas: bool


def executar_fluxo(pergunta: str, sessao_id: str = "default") -> ResultadoFluxo:
    """Executa o fluxo pedagógico completo para uma pergunta do estudante.

    Passos:
      1. Valida a entrada (nao vazia).
      2. Carrega a memoria da sessao.
      3. Classifica a intenção da pergunta.
      4. Detecta pedidos de invenção ou solução pronta (recusa educada).
      5. Detecta perguntas fora do escopo.
      6. Decide quais agentes participam.
      7. Monta e executa a crew CrewAI.
      8. O Guardiao revisa a resposta final (anti-alucinacao).
      9. Salva o turno na memoria.
      10. Retorna a resposta consolidada.
    """
    # 1. Valida entrada
    if not pergunta or not pergunta.strip():
        raise ErroEntradaVazia()

    pergunta = pergunta.strip()

    # 2. Carrega memoria da sessao
    memoria = MemoriaConversa(sessao_id)
    contexto = memoria.contexto_texto()

    # 3. Classifica a intenção
    intencao = classificar_intencao(pergunta)

    # 4. Detecta invenção de padrão (anti-alucinação)
    if intencao.tipo == "inventicao":
        raise ErroInventicao()

    # 5. Detecta pedido de solução pronta
    if intencao.tipo == "solucao_pronta":
        raise ErroSolucaoPronta()

    # 6. Detecta fora de escopo (heurística simples)
    if intencao.tipo == "fora_de_escopo":
        raise ErroForaDeEscopo(intencao.detalhe)

    # 7. Decide agentes
    agentes_ativos = decidir_agentes(intencao)

    # 8. Monta e executa a crew
    try:
        crew = montar_crew(agentes_ativos)
        entrada_crew = (
            f"{contexto}\n\n"
            f"Pergunta do estudante: {pergunta}\n\n"
            f"Intencao identificada: {intencao.tipo}\n"
            f"Responda em portugues do Brasil, focando no padrao Factory Method."
        )
        resultado = crew.kickoff(inputs={"pergunta": pergunta, "contexto": contexto, "entrada": entrada_crew})
        resposta = str(resultado)
    except (ErroEntradaVazia, ErroInventicao, ErroSolucaoPronta, ErroForaDeEscopo):
        raise
    except Exception as exc:  # falha do Ollama/modelo ou saída inesperada
        detalhe = str(exc) or type(exc).__name__
        if "ollama" in detalhe.lower() or "11434" in detalhe:
            raise ErroModeloIndisponivel(detalhe) from exc
        raise ErroSaidaInesperada(detalhe) from exc

    if not resposta or not resposta.strip():
        raise ErroSaidaInesperada("A crew retornou uma resposta vazia.")

    # 9. Salva o turno na memoria (ultimo agente ativo = guardiao se presente)
    agente_ultimo = agentes_ativos[-1] if agentes_ativos else "guardiao"
    memoria.salvar_turno(pergunta=pergunta, resposta=resposta, agente=agente_ultimo)

    return ResultadoFluxo(
        resposta=resposta,
        agente_ultimo=agente_ultimo,
        sessoes_atualizadas=True,
    )
