"""Classificacao heuristica da intencao da pergunta do estudante.

Usada pelo fluxo para decidir quais agentes participam. A classificacao
completa e refinada pode ser feita pelo proprio modelo local nas versoes
futuras; aqui mantemos simples e determinístico.
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

    # Invenção de padrão (anti-alucinação) — prioridade alta
    if contem(
        [
            "invente um padrão",
            "inventar um padrão",
            "padrão z",
            "padrão fictício",
            "criar um padrão",
            "padrão imaginário",
        ]
    ):
        return Intencao("inventicao", 0.95, "pedido de invenção de padrão")

    # Pedido de solução pronta
    if contem(
        [
            "código pronto",
            "solucao completa",
            "solucao pronta",
            "entrega o código",
            "copie e cole",
            "me entregue o código",
        ]
    ):
        return Intencao("solucao_pronta", 0.95, "pedido de solução pronta")

    # Conceito
    if contem(
        [
            "o que é",
            "o que e",
            "intencao",
            "problema que resolve",
            "participantes",
            "estrutura",
            "consequencia",
            "quando usar",
            "quando evitar",
            "para que serve",
        ]
    ):
        return Intencao("conceito", 0.85)

    # Exemplo em Java
    if contem(["exemplo", "em java", "codigo java", "aplicacao", "aplicação"]):
        return Intencao("exemplo", 0.85)

    # Exercício / diagnóstico
    if contem(
        [
            "exercício",
            "exercicio",
            "resposta",
            "diagnóstico",
            "diagnostico",
            "conceito equivocado",
            "confundido",
            "diferença",
            "diferenca",
            "simple factory",
            "abstract factory",
            "state",
            "strategy",
        ]
    ):
        return Intencao("diagnostico", 0.8)

    # Fechamento
    if contem(["lembrar", "fechamento", "antes de usar", "resumo", "o que devo lembrar"]):
        return Intencao("fechamento", 0.8)

    # Vocabulário do domínio Factory Method (usado para detectar fora de escopo)
    vocabulario_dominio = [
        "factory method",
        "fabrica",
        "fabrica metodo",
        "padrao de projeto",
        "padrão de projeto",
        "gof",
        "design pattern",
        "cria",
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
        "simple factory",
        "abstract factory",
        "metodo",
        "método",
        "method",
    ]

    def tem_vocabulario_dominio() -> bool:
        """Verifica se o texto contém palavras do domínio Factory Method."""
        return any(termo in p for termo in vocabulario_dominio)

    # Fora de escopo: não contém vocabulário do domínio e não foi
    # classificado como nenhuma intenção reconhecida acima.
    if not tem_vocabulario_dominio():
        return Intencao("fora_de_escopo", 0.7, "sem vocabulário do domínio Factory Method")

    # Default: conceito (apenas se há vocabulário do domínio, mas não
    # correspondeu a nenhuma intenção específica acima).
    return Intencao("conceito", 0.5, "intenção não identificada com certeza")


def decidir_agentes(intencao: Intencao) -> list[str]:
    """Decide quais agentes participam com base na intencao.

    O Guardiao está sempre presente (revisão final anti-alucinação).
    """
    mapeamento = {
        "conceito": ["tutor", "guardiao"],
        "exemplo": ["exemplificador", "guardiao"],
        "exercicio": ["inquiridor", "guardiao"],
        "diagnostico": ["inquiridor", "guardiao"],
        "fechamento": ["tutor", "guardiao"],
        "inventicao": ["guardiao"],
        "solucao_pronta": ["guardiao"],
        "fora_de_escopo": ["guardiao"],
    }
    return mapeamento.get(intencao.tipo, ["tutor", "guardiao"])
