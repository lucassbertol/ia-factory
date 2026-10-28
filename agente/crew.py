"""Montagem e coordenacao da crew CrewAI.

Construi os quatro agentes pedagógicos (tutor, exemplificador, inquiridor,
guardiao) como objetos Agent do CrewAI, define tarefas com dependências
entre elas e retorna um Crew pronto para execução.

Coordenação:
  - Processo sequencial com revisão final do Guardião.
  - O Guardião é sempre a última tarefa (revisa e consolida).
  - A pergunta do estudante e o contexto da conversa são injetados em TODAS
    as tarefas, para que cada agente responda ao que foi efetivamente pedido.
"""

from __future__ import annotations

from crewai import Agent, Crew, Process, Task

from .agentes import Tutor, Exemplificador, Inquiridor, Guardiao
from .config import PADRAO_ENSINADO
from .llm import obter_llm


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


def montar_crew(
    agentes_ativos: list[str] | None = None,
    pergunta: str = "",
    contexto: str = "",
    intencao: str = "",
) -> Crew:
    """Monta a crew CrewAI com os agentes informados.

    Args:
        agentes_ativos: lista de nomes de agentes a incluir
            (ex: ['tutor', 'guardiao']). Se None, inclui todos.
        pergunta: pergunta do estudante, injetada nas descricoes das tarefas.
        contexto: historico recente da conversa, injetado nas tarefas.
        intencao: intencao classificada (ex: 'exercicio'), usada como orientacao.

    Returns:
        Um objeto Crew configurado com agentes e tarefas.
    """
    if agentes_ativos is None:
        agentes_ativos = ["tutor", "exemplificador", "inquiridor", "guardiao"]

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

    # Blocos compartilhados por todas as tarefas
    contexto_sistema = (
        f"Voce faz parte de um sistema multiagente que ensina o padrao "
        f"{PADRAO_ENSINADO} a estudantes iniciantes. "
        f"Sempre responda em portugues do Brasil."
    )
    bloco_pergunta = f"Pergunta do estudante: {pergunta}\n\n"
    bloco_contexto = (
        f"Historico recente da conversa:\n{contexto}\n\n" if contexto else ""
    )
    bloco_intencao = (
        f"Intencao identificada: {intencao}. "
        f"Priorize exatamente o que o estudante pediu.\n\n"
        if intencao
        else ""
    )

    # Orientacao especifica para a intencao, usada pelo Inquiridor e pelo Guardiao
    orientacao_inquiridor = {
        "exercicio": (
            "O estudante pediu um EXERCICIO. Apresente SOMENTE o enunciado do "
            "exercicio (contexto + o que ele deve fazer) e uma pergunta guia. "
            "NAO mostre a solucao, NAO escreva codigo e NAO explique o conceito "
            "antes de o estudante tentar. Termine aguardando a resposta dele.\n\n"
        ),
        "diagnostico": (
            "O estudante quer entender um equivoco ou uma diferenca. Diagnostique "
            "a confusao, explique a diferenca de forma breve e faca uma pergunta "
            "guia. NAO entregue a solucao pronta.\n\n"
        ),
    }.get(intencao, "")

    orientacao_guardiao = {
        "exercicio": (
            "O estudante pediu um EXERCICIO: preserve o enunciado do exercicio e "
            "a pergunta guia. NAO substitua o exercicio por uma explicacao do "
            "conceito e NAO entregue a solucao. A resposta final deve terminar "
            "aguardando a resposta do estudante.\n\n"
        ),
        "diagnostico": (
            "O estudante quer um diagnostico: preserve a analise do equivoco e a "
            "pergunta guia, sem entregar a solucao pronta.\n\n"
        ),
        "exemplo": (
            "O estudante pediu um EXEMPLO: preserve o codigo Java e a explicacao "
            "produzidos pelo Exemplificador. NAO remova o codigo nem substitua "
            "por uma explicacao generica.\n\n"
        ),
    }.get(intencao, "")

    orientacao_tutor = {
        "conceito": (
            "Responda focando no aspecto do conceito que o estudante perguntou, "
            "sem despejar o conteudo inteiro.\n\n"
        ),
        "fechamento": (
            "O estudante pediu um RESUMO/FECHAMENTO: recapitule os pontos "
            "principais de forma curta, sem introduzir conteudo novo.\n\n"
        ),
    }.get(intencao, "")

    tarefas: list[Task] = []
    tarefa_anterior: Task | None = None

    # 1. Tutor — apresenta o conceito
    if "tutor" in agents_crewai:
        tarefa_tutor = Task(
            description=(
                f"{contexto_sistema}\n\n"
                f"{bloco_pergunta}"
                f"{bloco_contexto}"
                f"{bloco_intencao}"
                "Responda a pergunta do estudante acima apresentando o conceito "
                "do padrao Factory Method: intencao, problema resolvido, "
                "participantes, estrutura UML e consequencias. "
                "Se a pergunta for sobre um aspecto especifico, foque nesse aspecto "
                "sem repetir tudo o que ja foi dito no historico. "
                "Use o prompt de sistema do tutor como referencia.\n\n"
                f"{orientacao_tutor}"
            ),
            expected_output="Explicação clara e focada na pergunta do estudante, em português do Brasil.",
            agent=agents_crewai["tutor"],
        )
        tarefas.append(tarefa_tutor)
        tarefa_anterior = tarefa_tutor

    # 2. Exemplificador — fornece exemplo em Java
    if "exemplificador" in agents_crewai:
        tarefa_exemplificador = Task(
            description=(
                f"{contexto_sistema}\n\n"
                f"{bloco_pergunta}"
                f"{bloco_contexto}"
                f"{bloco_intencao}"
                "Responda a pergunta do estudante acima fornecendo um exemplo "
                "correto e idiomatico em Java do padrao Factory Method, "
                "explicando por que funciona e adaptando ao nivel do estudante. "
                "Use o prompt do exemplificador como referencia."
            ),
            expected_output="Exemplo em Java com explicacao, em portugues do Brasil.",
            agent=agents_crewai["exemplificador"],
            context=[tarefa_anterior] if tarefa_anterior else [],
        )
        tarefas.append(tarefa_exemplificador)
        tarefa_anterior = tarefa_exemplificador

    # 3. Inquiridor — conduz exercicio e diagnostica erros
    if "inquiridor" in agents_crewai:
        tarefa_inquiridor = Task(
            description=(
                f"{contexto_sistema}\n\n"
                f"{bloco_pergunta}"
                f"{bloco_contexto}"
                f"{bloco_intencao}"
                "Responda a pergunta do estudante acima conduzindo a pratica de "
                "forma socratica: proponha um exercicio pratico (ou avalie a "
                "resposta do estudante, se houver), detecte conceitos equivocados "
                "(ex.: confundir Factory Method com Simple Factory ou Abstract "
                "Factory) e oriente a correcao com perguntas guia. "
                "Use o prompt do inquiridor como referencia.\n\n"
                f"{orientacao_inquiridor}"
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
                f"{bloco_pergunta}"
                f"{bloco_contexto}"
                f"{bloco_intencao}"
                "Revise a resposta produzida pelos agentes anteriores para a "
                "pergunta do estudante: remova redundancias e contradicoes, "
                "confirme que nao ha invencao de fatos, padroes ou participantes "
                "inexistentes, aplique as regras anti-alucinacao e consolide o "
                "aprendizado. A resposta final deve responder diretamente ao que "
                "o estudante perguntou. "
                "Devolva APENAS a resposta final ao estudante: nao inclua "
                "comentarios sobre o processo de revisao, nao use rotulos como "
                "'Resposta final revisada' e nao explique o que voce fez. "
                "Use o prompt do guardiao como referencia.\n\n"
                f"{orientacao_guardiao}"
            ),
            expected_output="Resposta consolidada ao estudante, sem meta-comentarios, em portugues do Brasil.",
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
