"""Esqueleto do Agente 3 — Inquiridor e diagnosticador socratico.

A implementacao completa e feita nas etapas 3 e 4.
"""

from __future__ import annotations

from . import INQUISIDOR, AgenteDefinicao


class Inquiridor:
    """Agente inquiridor e diagnosticador de Factory Method."""

    def __init__(self) -> None:
        self.definicao: AgenteDefinicao = INQUISIDOR

    def resumo(self) -> str:
        return f"{self.definicao.role}: {self.definicao.goal}"
