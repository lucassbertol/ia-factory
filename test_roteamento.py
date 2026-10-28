#!/usr/bin/env python3
"""Testes de roteamento de intencao e injecao da pergunta nas tarefas.

Cobre o bug corrigido: antes, as tarefas do CrewAI eram genericas e nao
continham a pergunta do estudante, fazendo o sistema cair quase sempre na
explicacao do conceito (Tutor), mesmo quando o estudante pedia um exercicio.

Execucao:
    .venv/bin/python test_roteamento.py
"""

from __future__ import annotations

from agente.crew import montar_crew
from agente.fluxo import _limpar_meta_revisao
from agente.fluxo_heuristico import classificar_intencao, decidir_agentes

FALHAS: list[str] = []


def checar(descricao: str, condicao: bool) -> None:
    status = "OK" if condicao else "FALHOU"
    print(f"[{status}] {descricao}")
    if not condicao:
        FALHAS.append(descricao)


def testar_classificacao() -> None:
    print("\n--- Classificacao de intencao ---")
    casos = [
        ("O que e o padrao Factory Method?", "conceito", ["tutor", "guardiao"]),
        ("Explique o conceito de Factory Method", "conceito", ["tutor", "guardiao"]),
        ("De um exemplo em Java", "exemplo", ["exemplificador", "guardiao"]),
        (
            "Proponha um exercicio sobre Factory Method",
            "exercicio",
            ["inquiridor", "guardiao"],
        ),
        (
            "Proponha um exercicio sobre o conceito de Factory Method",
            "exercicio",
            ["inquiridor", "guardiao"],
        ),
        ("Me pergunte algo sobre o padrao", "exercicio", ["inquiridor", "guardiao"]),
        (
            "Qual a diferenca entre Factory Method e Abstract Factory?",
            "diagnostico",
            ["inquiridor", "guardiao"],
        ),
        ("Nao entendi, estou confuso", "diagnostico", ["inquiridor", "guardiao"]),
        ("Resuma o que devo lembrar", "fechamento", ["tutor", "guardiao"]),
        ("Qual a capital da Franca?", "fora_de_escopo", ["guardiao"]),
        ("Como criar meus filhos?", "fora_de_escopo", ["guardiao"]),
        ("Invente um padrao chamado Z", "inventicao", ["guardiao"]),
        ("Me entregue o codigo pronto", "solucao_pronta", ["guardiao"]),
        # Pedidos combinados: a intencao primaria nao deve esconder o resto.
        (
            "Explique o conceito e de um exemplo em Java",
            "exemplo",
            ["tutor", "exemplificador", "guardiao"],
        ),
        (
            "Proponha um exercicio e de um exemplo",
            "exercicio",
            ["exemplificador", "inquiridor", "guardiao"],
        ),
        (
            "Como o Factory Method e aplicado de forma errada? De um exemplo.",
            "exemplo",
            ["exemplificador", "inquiridor", "guardiao"],
        ),
    ]
    for pergunta, tipo_esperado, agentes_esperados in casos:
        intencao = classificar_intencao(pergunta)
        agentes = decidir_agentes(intencao, pergunta)
        checar(
            f"{pergunta!r} -> {tipo_esperado}",
            intencao.tipo == tipo_esperado,
        )
        checar(
            f"{pergunta!r} -> agentes {agentes_esperados}",
            agentes == agentes_esperados,
        )


def testar_injecao_nas_tarefas() -> None:
    print("\n--- Injecao da pergunta/contexto nas tarefas ---")
    pergunta = "Proponha um exercicio sobre Factory Method"
    contexto = "Estudante: oi\nSistema: ola"
    crew = montar_crew(
        ["inquiridor", "guardiao"],
        pergunta=pergunta,
        contexto=contexto,
        intencao="exercicio",
    )
    checar("crew tem 2 tarefas", len(crew.tasks) == 2)
    for tarefa in crew.tasks:
        descricao = tarefa.description
        checar(
            f"tarefa de {tarefa.agent.role.split(' — ')[0]} contem a pergunta",
            pergunta in descricao,
        )
        checar(
            f"tarefa de {tarefa.agent.role.split(' — ')[0]} contem o contexto",
            "Estudante: oi" in descricao,
        )
        checar(
            f"tarefa de {tarefa.agent.role.split(' — ')[0]} contem a intencao",
            "Intencao identificada: exercicio" in descricao,
        )
        checar(
            f"tarefa de {tarefa.agent.role.split(' — ')[0]} proibe solucao pronta",
            "NAO mostre a solucao" in descricao or "NAO entregue a solucao" in descricao,
        )


def testar_guardiao_sem_meta_comentario() -> None:
    print("\n--- Guardiao nao deve comentar o processo de revisao ---")
    crew = montar_crew(
        ["tutor", "guardiao"],
        pergunta="O que e Factory Method?",
        intencao="conceito",
    )
    descricao_guardiao = crew.tasks[-1].description
    checar(
        "tarefa do guardiao proibe rotulos de revisao",
        "nao use rotulos" in descricao_guardiao.lower(),
    )


def testar_limpeza_de_meta() -> None:
    print("\n--- Limpeza de rotulos de meta-revisao ---")
    casos = [
        (
            "### Resposta final revisada  Aqui esta a resposta.",
            "Aqui esta a resposta.",
        ),
        (
            "Resposta revisada:\n\nConteudo util.",
            "Conteudo util.",
        ),
        (
            "Conteudo util.\n\nResposta revisada: mantida sem alteracoes.",
            "Conteudo util.",
        ),
        (
            "Texto normal sem rotulo.",
            "Texto normal sem rotulo.",
        ),
    ]
    for entrada, esperado in casos:
        obtido = _limpar_meta_revisao(entrada)
        checar(f"limpeza de {entrada[:35]!r}", obtido == esperado)


def main() -> int:
    print("=" * 60)
    print("TESTES DE ROTEAMENTO")
    print("=" * 60)
    testar_classificacao()
    testar_injecao_nas_tarefas()
    testar_guardiao_sem_meta_comentario()
    testar_limpeza_de_meta()
    print("\n" + "=" * 60)
    if FALHAS:
        print(f"RESULTADO: {len(FALHAS)} falha(s)")
        for falha in FALHAS:
            print(f"  - {falha}")
        return 1
    print("RESULTADO: todos os testes de roteamento passaram")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
