"""Esqueleto do Agente 2 — Exemplificador (Java).

A implementacao completa e feita nas etapas 3 e 4.
"""

from __future__ import annotations

from . import EXEMPLIFICADOR, AgenteDefinicao


class Exemplificador:
    """Agente exemplificador de Factory Method em Java."""

    def __init__(self) -> None:
        self.definicao: AgenteDefinicao = EXEMPLIFICADOR

    def resumo(self) -> str:
        return f"{self.definicao.role}: {self.definicao.goal}"
