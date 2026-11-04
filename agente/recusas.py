"""Respostas determinísticas: recusas educadas, redirecionamentos e boas-vindas.

Esses casos não passam pelo modelo de linguagem de propósito. Um modelo de 3B
não recusa de forma confiável: diante de "explique o padrão Z" ele tende a
inventar uma explicação plausível. A recusa é a primeira barreira da defesa
anti-alucinação; as regras nos prompts e a verificação do Guardião são as
seguintes.

Toda recusa termina oferecendo um próximo passo, para não encerrar a aula, como
afirmação: perguntas ao estudante ficam só nos exercícios.
"""

from __future__ import annotations

from .config import PADRAO_ENSINADO


def boas_vindas() -> str:
    return (
        f"Olá! Eu sou um sistema de tutores que ensina o padrão {PADRAO_ENSINADO}. "
        "Trabalhamos em equipe: um tutor explica o conceito, um especialista em Java "
        "explica exemplos verificados, um tutor socrático propõe exercícios e um "
        "guardião confere cada resposta antes de ela chegar até você.\n\n"
        "Você pode pedir, por exemplo:\n"
        "- \"Explique o que é o Factory Method e qual problema ele resolve.\"\n"
        "- \"Dê um exemplo em Java.\"\n"
        "- \"Quando devo usar e quando devo evitar?\"\n"
        "- \"Qual a diferença para o Abstract Factory?\"\n"
        "- \"Proponha um exercício.\"\n\n"
        "Se quiser, conte o seu nível (\"sou iniciante\", \"sou intermediário\" ou "
        "\"sou avançado\") para eu ajustar as explicações."
    )


def padrao_inventado() -> str:
    return (
        "Não posso inventar um padrão de projeto. Se eu criasse um padrão "
        "e o explicasse como se fosse real, você poderia estudar e usar algo que não "
        "existe em nenhuma referência. Quando eu não sei algo, digo que não sei.\n\n"
        f"O que posso fazer é ensinar um padrão real do catálogo GoF: o {PADRAO_ENSINADO}. "
        "Posso começar pela ideia central dele ou por um exemplo em Java."
    )


def padrao_desconhecido(nome: str) -> str:
    return (
        f"Não conheço nenhum padrão de projeto chamado \"{nome}\" no catálogo GoF nem "
        "na minha referência, então não vou explicar algo que eu teria de inventar. "
        "Se esse nome apareceu em algum material, vale conferir a fonte original "
        "ou o material da disciplina.\n\n"
        f"Talvez você esteja pensando no {PADRAO_ENSINADO}, ou em padrões parecidos "
        "como Abstract Factory ou Simple Factory; posso explicar a diferença "
        "entre eles."
    )


def outro_padrao(nome: str) -> str:
    from .catalogo import INTENCOES_GOF, nome_canonico_gof
    from .fluxo_heuristico import _normaliza

    oficial = nome_canonico_gof(_normaliza(nome))
    if oficial:
        categoria, intencao = INTENCOES_GOF[oficial].split("; ", 1)
        resumo = (
            f"{oficial} é um padrão {categoria} do catálogo GoF. Em uma frase, ele "
            f"{intencao}. "
        )
    else:
        resumo = f"\"{nome}\" é um padrão real, mas não pertence ao catálogo GoF. "
    return (
        f"{resumo}Este sistema, porém, foi construído para ensinar apenas o "
        f"{PADRAO_ENSINADO}, e eu prefiro não aprofundar outro padrão sem uma "
        "referência verificada. Para ele, consulte o material da disciplina ou o "
        "sistema da dupla responsável por esse padrão.\n\n"
        f"Se a sua dúvida for como o {PADRAO_ENSINADO} se relaciona com outros "
        "padrões de criação, posso comparar com Abstract Factory, Simple Factory "
        "e Template Method."
    )


def solucao_pronta(exercicio_pendente: bool = False) -> str:
    inicio = (
        "Não vou entregar a resposta pronta do exercício: você aprende muito mais "
        "chegando lá com as próprias pernas, e eu te ajudo em cada passo."
        if exercicio_pendente else
        "Não entrego código pronto de uma solução completa, porque isso tiraria de "
        "você justamente a parte que ensina. Mas posso te guiar até lá."
    )
    return (
        f"{inicio}\n\n"
        "Um caminho em passos para aplicar o Factory Method:\n"
        "1. Identifique o que varia: qual objeto muda conforme o caso? Esse é o seu Product.\n"
        "2. Escreva a interface (ou classe base) do Product e uma classe para cada variação (ConcreteProducts).\n"
        "3. Crie o Creator com o método de criação (o factory method) e com a operação "
        "de negócio que usa o produto apenas pela interface.\n"
        "4. Crie uma subclasse do Creator para cada variação (ConcreteCreators), "
        "sobrescrevendo só o método de criação.\n"
        "5. Teste: adicionar uma nova variação deve exigir classes novas, sem editar a "
        "operação de negócio.\n\n"
        "Me mostre a sua tentativa de qualquer passo e eu te dou um retorno."
    )


def fora_de_escopo() -> str:
    return (
        f"Essa pergunta está fora do que eu ensino: sou especializado no padrão de "
        f"projeto {PADRAO_ENSINADO}. Para outros assuntos, consulte o material da "
        "disciplina ou outra fonte confiável.\n\n"
        "Sobre o Factory Method, posso explicar o conceito, mostrar um exemplo em Java, "
        "comparar com padrões parecidos ou propor um exercício."
    )


def resposta_nao_validada() -> str:
    """Saída segura sem expor os rascunhos reprovados ou inconclusivos."""
    return (
        "Não consegui validar uma resposta para essa pergunta. "
        "Você pode reformular a pergunta ou consultar o material da disciplina."
    )
