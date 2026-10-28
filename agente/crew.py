"""Montagem e coordenacao da crew CrewAI.

Construi os quatro agentes pedagógicos (tutor, exemplificador, inquiridor,
guardiao) como objetos Agent do CrewAI, define tarefas com dependências
entre elas e retorna um Crew pronto para execução.

Coordenação:
  - Processo sequencial com revisão final do Guardião.
  - O Guardião é sempre a última tarefa (revisa e consolida).
  - Dependências: tutor -> exemplificador -> inquiridor -> guardiao,
    conforme a intenção da pergunta do estudante.
"""

from __future__ import annotations

from crewai import Agent, Crew, Process, Task

from .agentes import AGENTES, Tutor, Exemplificador, Inquiridor, Guardiao
from .config import PADRAO_ENSINADO
from .llm import obter_llm
from .prompts import carregar_prompt


def _criar_agent(agente_instancia) -> Agent:
    """Cria um Agent do CrewAI a partir de uma definicao de agente."""
    definicao = agente_instancia.definicao
    return Agent(
        role=definicao.role,
        goal=definicao.goal,
        backstory=definicao.backstory,
        llm=obter_llm(),
        verbose=False,
        allow_delegation=False,
        max_iter=2,
    )


def montar_crew(agentes_ativos: list[str] | None = None) -> Crew:
    """Monta a crew CrewAI com os agentes informados.

    Args:
        agentes_ativos: lista de nomes de agentes a incluir
            (ex: ['tutor', 'guardiao']). Se None, inclui todos.

    Returns:
        Um objeto Crew configurado com agentes e tarefas.
    """
    if agentes_ativos is None:
        agentes_ativos = ["tutor", "exemplificador", "inquiridor", "guardiao"]

    # Instancia os agentes solicitados
    instancias: dict[str, object] = {
        "tutor": Tutor(),
        "exemplificador": Exemplificador(),
        "inquiridor": Inquiridor(),
        "guardiao": Guardiao(),
    }

    agents_crewai: dict[str, Agent] = {}
    for nome in agentes_ativos:
        if nome in instancias:
            agents_crewai[nome] = _criar_agent(instancias[nome])

    # Contexto de sistema compartilhado (padrao ensinado)
    contexto_sistema = (
        f"Voce faz parte de um sistema multiagente que ensina o padrao "
        f"{PADRAO_ENSINADO} a estudantes iniciantes. "
        f"Sempre responda em portugues do Brasil."
    )

    tarefas: list[Task] = []
    tarefa_anterior: Task | None = None

    # 1. Tutor — apresenta o conceito quando relevante
    if "tutor" in agents_crewai:
        tarefa_tutor = Task(
            description=(
                f"{contexto_sistema}\n\n"
                "Apresente o conceito do padrao Factory Method: intencao, "
                "problema resolvido, participantes, estrutura UML e consequencias. "
                "Use o prompt de sistema do tutor como referencia."
            ),
            expected_output="Explicação clara do Factory Method em português do Brasil.",
            agent=agents_crewai["tutor"],
        )
        tarefas.append(tarefa_tutor)
        tarefa_anterior = tarefa_tutor

    # 2. Exemplificador — fornece exemplo em Java quando relevante
    if "exemplificador" in agents_crewai:
        tarefa_exemplificador = Task(
            description=(
                f"{contexto_sistema}\n\n"
                "Forneca um exemplo correto e idiomatico em Java do padrao "
                "Factory Method, explicando por que funciona e adaptando ao "
                "nivel do estudante. Use o prompt do exemplificador como referencia."
            ),
            expected_output="Exemplo em Java com explicacao, em portugues do Brasil.",
            agent=agents_crewai["exemplificador"],
            context=[tarefa_anterior] if tarefa_anterior else [],
        )
        tarefas.append(tarefa_exemplificador)
        tarefa_anterior = tarefa_exemplificador

    # 3. Inquiridor — conduz exercicio e diagnostica erros quando relevante
    if "inquiridor" in agents_crewai:
        tarefa_inquiridor = Task(
            description=(
                f"{contexto_sistema}\n\n"
                "Proponha um exercicio pratico, avalie a resposta do estudante, "
                "detecte conceitos equivocados (ex.: confundir Factory Method com "
                "Simple Factory ou Abstract Factory) e oriente a correcao de forma "
                "socratica. Use o prompt do inquiridor como referencia."
            ),
            expected_output="Exercicio, avaliacao e feedback socratico em portugues do Brasil.",
            agent=agents_crewai["inquiridor"],
            context=[tarefa_anterior] if tarefa_anterior else [],
        )
        tarefas.append(tarefa_inquiridor)
        tarefa_anterior = tarefa_inquiridor

    # 4. Guardiao — revisa a resposta final (SEMPRE ultima, aplica anti-alucinacao)
    if "guardiao" in agents_crewai:
        tarefa_guardiao = Task(
            description=(
                f"{contexto_sistema}\n\n"
                "Revise a conversa e a resposta final: remova redundancias e "
                "contradicoes entre agentes, confirme que nao ha invencao de "
                "fatos, padroes ou participantes inexistentes, aplique as regras "
                "anti-alucinacao e consolidate o aprendizado. "
                "Use o prompt do guardiao como referencia."
            ),
            expected_output="Resposta final revisada, coerente e confiavel em portugues do Brasil.",
            agent=agents_crewai["guardiao"],
            context=[tarefa_anterior] if tarefa_anterior else [],
        )
        tarefas.append(tarefa_guardiao)
        tarefa_anterior = tarefa_guardiao

    crew = Crew(
        agents=list(agents_crewai.values()),
        tasks=tarefas,
        process=Process.sequential,
        verbose=False,
    )
    return crew
