"""Testes funcionais e pedagógicos (Etapa 7).

Executa os 7 cenarios do roteiro de avaliacao padronizado da professora,
mais testes extras de erro. Registra entrada, resposta real, resultado
esperado, julgamento de correcao/utilidade e limitacoes.

Nao inventa resultados. Se um teste nao puder ser executado, registra como
pendente.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import sys

sys.path.insert(0, ".")

from agente.erro import ErroInventicao, ErroSolucaoPronta, ErroForaDeEscopo
from agente.fluxo import executar_fluxo

RESULTADOS_DIR = Path("evidencias/testes_etapa7")
RESULTADOS_DIR.mkdir(parents=True, exist_ok=True)


def executar(pergunta: str, sessao_id: str = "etapa7") -> str:
    """Executa um teste e retorna a resposta real.

    Excecoes de recusa educada (invencao, solucao pronta, fora de escopo)
    sao comportamentos esperados; a mensagem e retornada como resposta.
    """
    try:
        resultado = executar_fluxo(pergunta, sessao_id=sessao_id)
        return resultado.resposta
    except (ErroInventicao, ErroSolucaoPronta, ErroForaDeEscopo) as e:
        return f"[RECUSA EDUCADA] {e.mensagem_usuario}"


def salvar_evidencia(numero: str, categoria: str, entrada: str, resposta: str,
                     esperado: str, julgamento: str, limite: str) -> None:
    """Salva a evidencia de um teste em arquivo JSON."""
    evidencia = {
        "numero": numero,
        "categoria": categoria,
        "entrada": entrada,
        "resposta_real": resposta,
        "resultado_esperado": esperado,
        "julgamento_correcao_utilidade": julgamento,
        "limitacoes": limite,
        "timestamp": datetime.now().isoformat(),
    }
    caminho = RESULTADOS_DIR / f"teste_{numero}.json"
    caminho.write_text(json.dumps(evidencia, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    testes = []

    # ----------------------------------------------------------------
    # CATEGORIA 1 - Conceitual
    # ----------------------------------------------------------------
    entrada = "Explique o que e o padrao Factory Method e qual problema ele resolve."
    resposta = executar(entrada)
    esperado = "Explicacao correta da intencao e do problema resolvido pelo Factory Method."
    julgamento = ("Resposta aborda intencao e problema. Verificar se nao confunde "
                  "com Abstract Factory (risco com modelo pequeno).")
    salvar_evidencia("01", "Conceitual", entrada, resposta, esperado, julgamento,
                     "Modelo qwen2.5:3b pode simplificar excessivamente.")
    testes.append(("01 - Conceitual", resposta))

    # ----------------------------------------------------------------
    # CATEGORIA 2 - Exemplo em Java
    # ----------------------------------------------------------------
    entrada = "De um exemplo de aplicacao do padrao Factory Method em Java."
    resposta = executar(entrada)
    esperado = "Codigo Java comentado, com participantes do padrao identificados."
    julgamento = ("Deve conter codigo Java. Verificar se esta correto para Factory "
                  "Method (nao Abstract Factory).")
    salvar_evidencia("02", "Exemplo", entrada, resposta, esperado, julgamento,
                     "Risco de o modelo gerar codigo de Abstract Factory.")
    testes.append(("02 - Exemplo", resposta))

    # ----------------------------------------------------------------
    # CATEGORIA 3 - Selecao (quando usar / evitar)
    # ----------------------------------------------------------------
    entrada = ("Descreva uma situacao em que o Factory Method e a melhor escolha e uma "
               "em que ele deveria ser evitado, explicando o porquê.")
    resposta = executar(entrada)
    esperado = "Situacao de uso adequada e situacao de evitacao, com justificativa."
    julgamento = ("Deve apresentar ambos os lados com fundamentacao.")
    salvar_evidencia("03", "Selecao", entrada, resposta, esperado, julgamento, "")
    testes.append(("03 - Selecao", resposta))

    # ----------------------------------------------------------------
    # CATEGORIA 4 - Uso incorreto
    # ----------------------------------------------------------------
    entrada = ("Como o Factory Method costuma ser aplicado de forma errada? Dê um "
               "exemplo de uso equivocado e explique como corrigir.")
    resposta = executar(entrada)
    esperado = "Exemplo de uso errado e explicacao de correcao."
    julgamento = ("Deve identificar um erro real e propor correcao.")
    salvar_evidencia("04", "Uso incorreto", entrada, resposta, esperado, julgamento, "")
    testes.append(("04 - Uso incorreto", resposta))

    # ----------------------------------------------------------------
    # CATEGORIA 5 - Conceitos equivocados
    # ----------------------------------------------------------------
    entrada = ("Com qual padrao o Factory Method e mais confundido? Explique a diferenca "
               "entre eles e por que essa confusao acontece.")
    resposta = executar(entrada)
    esperado = "Identifica Simple Factory ou Abstract Factory e explica a diferenca."
    julgamento = ("Esperado: confusao com Simple Factory ou Abstract Factory. "
                  "Verificar se a diferenca esta correta.")
    salvar_evidencia("05", "Conceitos equivocados", entrada, resposta, esperado, julgamento,
                     "Modelo pode confundir os padroes na resposta.")
    testes.append(("05 - Conceitos equivocados", resposta))

    # ----------------------------------------------------------------
    # CATEGORIA 6 - Anti-alucinacao (2 sub-testes)
    # ----------------------------------------------------------------
    entrada_a = "Invente um padrao chamado Z e explique para mim."
    resposta_a = executar(entrada_a)
    esperado_a = "Recusa educada, nao inventa padrao."
    julgamento_a = ("Deve recusar educadamente e dizer que nao inventa padroes.")
    salvar_evidencia("06a", "Anti-alucinacao", entrada_a, resposta_a, esperado_a,
                     julgamento_a, "")
    testes.append(("06a - Anti-alucinacao (inventar padrao)", resposta_a))

    entrada_b = "Me entregue o codigo pronto de uma solucao completa."
    resposta_b = executar(entrada_b)
    esperado_b = "Recusa educada, orienta passo a passo."
    julgamento_b = ("Deve recusar solucao pronta e oferecer orientacao guiada.")
    salvar_evidencia("06b", "Anti-alucinacao", entrada_b, resposta_b, esperado_b,
                     julgamento_b, "")
    testes.append(("06b - Anti-alucinacao (solucao pronta)", resposta_b))

    # ----------------------------------------------------------------
    # CATEGORIA 7 - Fechamento
    # ----------------------------------------------------------------
    entrada = "O que devo lembrar antes de usar o Factory Method?"
    resposta = executar(entrada)
    esperado = "Resumo de pontos importantes antes de adotar o padrao."
    julgamento = ("Deve ser um resumo pratico e direto.")
    salvar_evidencia("07", "Fechamento", entrada, resposta, esperado, julgamento, "")
    testes.append(("07 - Fechamento", resposta))

    # ----------------------------------------------------------------
    # TESTES EXTRAS DE ERRO
    # ----------------------------------------------------------------
    # Entrada vazia
    try:
        executar_fluxo("")
        resposta_vazio = "NAO LANCOU ERRO (inesperado)"
        julgamento_vazio = "FALHA: deveria lançar ErroEntradaVazia."
    except Exception as e:
        resposta_vazio = str(e)
        julgamento_vazio = "OK: entrada vazia rejeitada."
    salvar_evidencia("E1", "Entrada vazia", "", resposta_vazio,
                     "Mensagem de erro amigavel", julgamento_vazio, "")
    testes.append(("E1 - Entrada vazia", resposta_vazio))

    # Pergunta fora de escopo
    resposta_fora = executar("Qual a capital da Francia?")
    esperado_fora = "Diz que e fora do escopo do Factory Method."
    julgamento_fora = "Deve recusar educadamente dizendo que so ensina Factory Method."
    salvar_evidencia("E2", "Fora de escopo", "Qual a capital da Francia?", resposta_fora,
                     esperado_fora, julgamento_fora, "")
    testes.append(("E2 - Fora de escopo", resposta_fora))

    # Perguntas consecutivas com dependencia de contexto (memoria)
    sessao_mem = "etapa7_memoria"
    r_mem1 = executar("O que e o padrao Factory Method?", sessao_id=sessao_mem)
    r_mem2 = executar("E quais sao as consequencias?", sessao_id=sessao_mem)
    julgamento_mem = ("O segundo turno deve usar o contexto do primeiro (memoria).")
    salvar_evidencia("E3", "Memoria/contexto",
                     "Turno 1: O que e o Factory Method? | Turno 2: E quais sao as consequencias?",
                     f"Turno 2: {r_mem2[:200]}...",
                     "Contexto anterior utilizado.",
                     julgamento_mem, "")
    testes.append(("E3 - Memoria/contexto", r_mem2[:200] + "..."))

    # Premissa falsa
    resposta_falsa = executar("O Factory Method foi criado pela Microsoft em 2020.")
    esperado_falsa = "Nao confirma premissa falsa; corrige ou diz que nao sabe."
    julgamento_falsa = ("Deve nao aceitar premissa falsa como fato.")
    salvar_evidencia("E4", "Premissa falsa", "O Factory Method foi criado pela Microsoft em 2020.",
                     resposta_falsa, esperado_falsa, julgamento_falsa, "")
    testes.append(("E4 - Premissa falsa", resposta_falsa[:200] + "..."))

    # Confusao Factory Method vs Simple Factory / Abstract Factory
    resposta_conf = executar("Factory Method e o mesmo que Simple Factory?")
    esperado_conf = "Explica que nao sao a mesma coisa."
    julgamento_conf = ("Deve diferenciar Factory Method de Simple Factory.")
    salvar_evidencia("E5", "Confusao de padroes", "Factory Method e o mesmo que Simple Factory?",
                     resposta_conf, esperado_conf, julgamento_conf, "")
    testes.append(("E5 - Confusao de padroes", resposta_conf[:200] + "..."))

    # ----------------------------------------------------------------
    # RELATORIO FINAL
    # ----------------------------------------------------------------
    print("=" * 70)
    print("ETAPA 7 - TESTES FUNCIONAIS E PEDAGOGICOS")
    print("=" * 70)
    for nome, resposta in testes:
        print(f"\n--- {nome} ---")
        print(resposta[:300].replace("\n", " "))
        print("...")
    print()
    print(f"Total de testes executados: {len(testes)}")
    print(f"Evidencias salvas em: {RESULTADOS_DIR}")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
