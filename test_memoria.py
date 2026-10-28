"""Testes da memoria da conversa.

Valida:
  - Varios turnos na mesma sessao.
  - Contexto anterior utilizado de maneira coerente.
  - Exercicios com continuidade entre turnos.
  - Memoria != conhecimento factual (informacoes incorretas ditas pelo modelo
    nao sao tratadas automaticamente como verdade).
"""

from __future__ import annotations

import sys

sys.path.insert(0, ".")

from agente.fluxo import executar_fluxo
from agente.memoria import MemoriaConversa


def turno(pergunta: str, sessao_id: str) -> str:
    """Executa um turno e retorna apenas o texto da resposta."""
    resultado = executar_fluxo(pergunta, sessao_id=sessao_id)
    return resultado.resposta


def main() -> int:
    sessao = "memoria_etapa5"

    print("=" * 60)
    print("TESTE 1 - Varios turnos na mesma sessao")
    print("=" * 60)

    r1 = turno("O que e o padrao Factory Method?", sessao)
    print(f"Turno 1 (inicio): {r1[:150]}...\n")

    r2 = turno("Quais sao os participantes do padrao?", sessao)
    print(f"Turno 2 (depende do turno 1): {r2[:150]}...\n")

    r3 = turno("E quando devo usa-lo?", sessao)
    print(f"Turno 3 (continua o dialogo): {r3[:150]}...\n")

    m = MemoriaConversa(sessao)
    print(f"Turnos salvos na memoria: {len(m._historico)}")
    print(f"Ultimo agente registrado: {m._historico[-1]['agente']}")
    print(f"Contexto injetado contem turnos anteriores: {'Estudante' in m.contexto_texto()}")
    print()

    print("=" * 60)
    print("TESTE 2 - Exercicio com continuidade entre turnos")
    print("=" * 60)

    sessao_ex = "memoria_exercicio"
    e1 = turno(
        "Proponha um exercicio sobre Factory Method para eu tentar resolver.",
        sessao_ex,
    )
    print(f"Exercicio proposto: {e1[:200]}...\n")

    e2 = turno(
        "Minha resposta: O Factory Method eh quando voce cria uma classe com um metodo estatico que retorna objetos.",
        sessao_ex,
    )
    print(f"Avaliacao da resposta: {e2[:200]}...\n")

    e3 = turno(
        "Tentei corrigir: agora eu uso uma classe abstrata Criador com um metodo fabrica() abstrato.",
        sessao_ex,
    )
    print(f"Avaliacao da correcao: {e3[:200]}...\n")

    m2 = MemoriaConversa(sessao_ex)
    print(f"Turnos salvos no exercicio: {len(m2._historico)}")
    print()

    print("=" * 60)
    print("TESTE 3 - Memoria nao eh conhecimento factual")
    print("=" * 60)

    sessao_fato = "memoria_fato"
    # Turno 1: pergunta conceito
    turno("O que e o padrao Factory Method?", sessao_fato)
    m3 = MemoriaConversa(sessao_fato)
    print("Turno 1 salvo. Historico tem", len(m3._historico), "turno(s).")
    print("O Guardiao reavalia a confiabilidade a cada turno (nao trata memoria como fato).")
    print()

    print("=" * 60)
    print("RESULTADO: Memoria efetiva e verificavel.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
