"""Esqueleto do Agente 1 — Tutor do conceito.

A implementacao completa do prompt e da integracao com o CrewAI e feita
nas etapas 3 e 4. Aqui fica apenas a definicao do papel e um metodo de
exibicao para documentacao.
"""

from __future__ import annotations

from . import TUTOR, AgenteDefinicao


class Tutor:
    """Agente tutor do conceito do Factory Method."""

    def __init__(self) -> None:
        self.definicao: AgenteDefinicao = TUTOR

    def resumo(self) -> str:
        return f"{self.definicao.role}: {self.definicao.goal}"
