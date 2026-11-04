"""Carregamento dos prompts de sistema dos agentes (agente/prompts/*.txt)."""

from __future__ import annotations

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent
VALIDOS = ("tutor", "exemplificador", "inquiridor", "guardiao")


def carregar_prompt(nome_agente: str) -> str:
    """Conteúdo integral do prompt de sistema do agente informado."""
    if nome_agente not in VALIDOS:
        raise ValueError(f"Agente inválido: {nome_agente}. Válidos: {list(VALIDOS)}")
    caminho = PROMPTS_DIR / f"{nome_agente}.txt"
    if not caminho.exists():
        raise FileNotFoundError(f"Prompt não encontrado: {caminho}")
    texto = caminho.read_text(encoding="utf-8")
    if not texto.strip():
        raise ValueError(f"Prompt vazio: {caminho}")
    return texto
