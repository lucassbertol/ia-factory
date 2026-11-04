"""Definição dos quatro agentes pedagógicos.

Fonte única: os arquivos agente/prompts/<nome>.txt. Cada arquivo segue o
esqueleto do Anexo B da especificação (ROLE, GOAL, BACKSTORY, ESCOPO,
ESTRATÉGIA PEDAGÓGICA, EXEMPLOS, CASOS DE ERRO, REGRAS ANTI-ALUCINAÇÃO,
FORMATO DAS RESPOSTAS). Este módulo separa ROLE, GOAL e BACKSTORY, que o
CrewAI recebe em campos próprios; as demais seções vão junto com o backstory,
seguidas da referência conceitual local.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from ..prompts import carregar_prompt

NOMES = ("tutor", "exemplificador", "inquiridor", "guardiao")

TITULOS = {
    "tutor": "Tutor do conceito",
    "exemplificador": "Exemplificador",
    "inquiridor": "Inquiridor",
    "guardiao": "Guardião",
}


@dataclass(frozen=True)
class DefinicaoAgente:
    nome: str
    role: str
    goal: str
    backstory: str
    instrucoes: str  # seções ESCOPO ... FORMATO DAS RESPOSTAS

    @property
    def titulo(self) -> str:
        return TITULOS[self.nome]


def _campo(texto: str, rotulo: str) -> str:
    achado = re.search(rf"^{rotulo}:\s*(.+)$", texto, re.MULTILINE)
    if not achado:
        raise ValueError(f"Campo {rotulo} ausente no prompt")
    return achado.group(1).strip()


def carregar_definicao(nome: str) -> DefinicaoAgente:
    texto = carregar_prompt(nome)
    inicio_secoes = re.search(r"^ESCOPO\s*$", texto, re.MULTILINE)
    if not inicio_secoes:
        raise ValueError(f"Seção ESCOPO ausente em prompts/{nome}.txt")
    return DefinicaoAgente(
        nome=nome,
        role=_campo(texto, "ROLE"),
        goal=_campo(texto, "GOAL"),
        backstory=_campo(texto, "BACKSTORY"),
        instrucoes=texto[inicio_secoes.start():].strip(),
    )


__all__ = ["NOMES", "TITULOS", "DefinicaoAgente", "carregar_definicao"]
