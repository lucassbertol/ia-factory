"""Classificacao heuristica da intencao da pergunta do estudante.

Usada pelo fluxo para decidir quais agentes participam. A classificacao
completa e refinada pode ser feita pelo proprio modelo local nas versoes
futuras; aqui mantemos simples e determinístico.

Ordem de prioridade (a primeira que casar vence):
  1. invencao / solucao_pronta  (anti-alucinacao)
  2. exercicio                  (pedido explicito de pratica)
  3. exemplo                    (pedido explicito de exemplo/codigo)
  4. diagnostico                (duvida, confusao, uso incorreto, comparacao)
  5. fechamento                 (resumo/retomada)
  6. conceito                   (explicacao do padrao)
  7. fora_de_escopo             (sem vocabulario do dominio)
  8. conceito (default)         (tem vocabulario do dominio, mas nao casou)
"""

from __future__ import annotations

from dataclasses import dataclass

import unicodedata


def _normaliza(texto: str) -> str:
    """Remove acentos e deixa minusculo para comparacao robusta."""
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


@dataclass
class Intencao:
    """Classificacao da intencao da pergunta do estudante."""

    tipo: str  # conceito | exemplo | exercicio | diagnostico | fechamento | fora_de_escopo | inventicao | solucao_pronta
    confianca: float
    detalhe: str = ""


def classificar_intencao(pergunta: str) -> Intencao:
    """Classifica a intencao da pergunta (heurístico por palavras-chave)."""
    p = _normaliza(pergunta)

    def contem(frases: list[str]) -> bool:
        """Verifica se alguma frase (normalizada) esta contida no texto."""
        return any(_normaliza(f) in p for f in frases)

    # 1a. Invenção de padrão (anti-alucinação) — prioridade alta
    if contem(
        [
            "invente um padrão",
            "invente um padrao",
            "inventar um padrão",
            "inventar um padrao",
            "padrão z",
            "padrao z",
            "padrão fictício",
            "padrao ficticio",
            "criar um padrão",
            "criar um padrao",
            "padrão imaginário",
            "padrao imaginario",
        ]
    ):
        return Intencao("inventicao", 0.95, "pedido de invenção de padrão")

    # 1b. Pedido de solução pronta
    if contem(
        [
            "código pronto",
            "codigo pronto",
            "solucao completa",
            "solução completa",
            "solucao pronta",
            "solução pronta",
            "entrega o código",
            "entrega o codigo",
            "copie e cole",
            "me entregue o código",
            "me entregue o codigo",
        ]
    ):
        return Intencao("solucao_pronta", 0.95, "pedido de solução pronta")

    # 2. Exercício — pedido explícito de prática
    if contem(
        [
            "exercício",
            "exercicio",
            "proponha",
            "proponha um",
            "proposto",
            "pratique",
            "praticar",
            "resolva",
            "resolver",
            "tarefa",
            "desafio",
            "atividade",
            "quiz",
            "pergunta para mim",
            "me pergunte",
        ]
    ):
        return Intencao("exercicio", 0.85, "pedido de exercício prático")

    # 3. Exemplo — pedido explícito de exemplo/código
    if contem(
        [
            "exemplo",
            "exemplos",
            "em java",
            "código java",
            "codigo java",
            "mostre o código",
            "mostre o codigo",
            "mostre como",
            "demonstre",
            "ilustre",
            "aplicação prática",
            "aplicacao pratica",
        ]
    ):
        return Intencao("exemplo", 0.85, "pedido de exemplo")

    # 4. Diagnóstico — dúvida, confusão, uso incorreto, comparação
    if contem(
        [
            "diagnóstico",
            "diagnostico",
            "conceito equivocado",
            "confundido",
            "confundo",
            "estou confuso",
            "não entendi",
            "nao entendi",
            "diferença",
            "diferenca",
            "comparação",
            "comparacao",
            "comparar",
            "errado",
            "errada",
            "incorreto",
            "incorreta",
            "má prática",
            "ma pratica",
            "antipadrão",
            "antipadrao",
            "simple factory",
            "abstract factory",
            "state",
            "strategy",
            "quando não usar",
            "quando nao usar",
            "limitações",
            "limitacoes",
        ]
    ):
        return Intencao("diagnostico", 0.8, "pedido de diagnóstico/comparação")

    # 5. Fechamento
    if contem(
        [
            "lembrar",
            "fechamento",
            "antes de usar",
            "resumo",
            "resumir",
            "o que devo lembrar",
            "recapitular",
            "conclusão",
            "conclusao",
        ]
    ):
        return Intencao("fechamento", 0.8, "pedido de fechamento/resumo")

    # 6. Conceito — explicação do padrão
    if contem(
        [
            "o que é",
            "o que e",
            "explique",
            "explicar",
            "intencao",
            "intenção",
            "problema que resolve",
            "participantes",
            "estrutura",
            "consequencia",
            "consequência",
            "quando usar",
            "quando evitar",
            "para que serve",
            "como funciona",
            "definição",
            "definicao",
            "conceito",
        ]
    ):
        return Intencao("conceito", 0.85, "pedido de explicação do conceito")

    # 7. Vocabulário do domínio Factory Method (usado para detectar fora de escopo)
    vocabulario_dominio = [
        "factory method",
        "factory",
        "fabrica",
        "fábrica",
        "padrao de projeto",
        "padrão de projeto",
        "gof",
        "design pattern",
        "criacao",
        "criação",
        "instancia",
        "instância",
        "objeto",
        "classe",
        "produto",
        "concreto",
        "abstrato",
        "criador",
        "heranca",
        "herança",
        "polimorfismo",
        "encapsulamento",
        "acoplamento",
        "metodo",
        "método",
        "method",
        "poo",
        "orientacao a objetos",
        "orientação a objetos",
    ]

    def tem_vocabulario_dominio() -> bool:
        """Verifica se o texto contém palavras do domínio Factory Method."""
        return any(_normaliza(termo) in p for termo in vocabulario_dominio)

    # 7. Fora de escopo: não contém vocabulário do domínio e não foi
    # classificado como nenhuma intenção reconhecida acima.
    if not tem_vocabulario_dominio():
        return Intencao(
            "fora_de_escopo",
            0.7,
            "sem vocabulário do domínio Factory Method",
        )

    # 8. Default: conceito (tem vocabulário do domínio, mas não casou
    # nenhuma intenção específica acima).
    return Intencao("conceito", 0.5, "intenção não identificada com certeza")


def decidir_agentes(intencao: Intencao, pergunta: str = "") -> list[str]:
    """Decide quais agentes participam com base na intencao e na pergunta.

    A intencao primaria define o agente principal. Pedidos adicionais
    explicitos na mesma pergunta (ex.: "explique e de um exemplo") acrescentam
    os agentes correspondentes, mantendo a ordem pedagogica
    tutor -> exemplificador -> inquiridor -> guardiao.

    O Guardiao está sempre presente (revisão final anti-alucinação).
    """
    base_por_intencao = {
        "conceito": ["tutor"],
        "exemplo": ["exemplificador"],
        "exercicio": ["inquiridor"],
        "diagnostico": ["inquiridor"],
        "fechamento": ["tutor"],
        "inventicao": [],
        "solucao_pronta": [],
        "fora_de_escopo": [],
    }
    base = base_por_intencao.get(intencao.tipo, ["tutor"])

    # Pedidos de recusa/anti-alucinacao nao recebem outros agentes.
    if not base:
        return ["guardiao"]

    p = _normaliza(pergunta)

    def contem_termos(termos: list[str]) -> bool:
        return any(_normaliza(t) in p for t in termos)

    pede_exemplo = contem_termos(
        ["exemplo", "em java", "codigo java", "código java", "mostre o codigo"]
    )
    pede_diagnostico = contem_termos(
        [
            "errado",
            "errada",
            "incorreto",
            "incorreta",
            "confundido",
            "confundo",
            "diferenca",
            "diferença",
            "equivocado",
            "ma pratica",
            "má prática",
            "antipadrao",
            "antipadrão",
        ]
    )
    pede_exercicio = contem_termos(
        [
            "exercicio",
            "exercício",
            "proponha",
            "pratique",
            "praticar",
            "resolva",
            "desafio",
            "atividade",
            "quiz",
        ]
    )
    pede_conceito = contem_termos(
        [
            "explique",
            "explicar",
            "o que e",
            "o que é",
            "como funciona",
            "definicao",
            "definição",
        ]
    )

    extras: set[str] = set()
    if pede_exemplo and "exemplificador" not in base:
        extras.add("exemplificador")
    if (pede_diagnostico or pede_exercicio) and "inquiridor" not in base:
        extras.add("inquiridor")
    if pede_conceito and "tutor" not in base:
        extras.add("tutor")

    ativos = set(base) | extras
    ordenados = [nome for nome in ("tutor", "exemplificador", "inquiridor") if nome in ativos]
    return ordenados + ["guardiao"]
