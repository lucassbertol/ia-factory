"""Esqueleto do Agente 4 — Guardiao e revisor de confiabilidade.

A implementacao completa e feita nas etapas 3 e 4.
"""

from __future__ import annotations

from . import GUARDIÃO, AgenteDefinicao


class Guardiao:
    """Agente guardiao e revisor de confiabilidade."""

    def __init__(self) -> None:
        self.definicao: AgenteDefinicao = GUARDIÃO

    def resumo(self) -> str:
        return f"{self.definicao.role}: {self.definicao.goal}"
