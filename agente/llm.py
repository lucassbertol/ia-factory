"""Configuracao do LLM local (Ollama) para uso pelos agentes CrewAI.

Tudo roda localmente, sem API paga, sem servico de nuvem, sem custo.
"""

from __future__ import annotations

from crewai import LLM

from .config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT_SEGUNDOS


def obter_llm() -> LLM:
    """Retorna uma instancia do LLM configurada para o Ollama local.

    O modelo qwen2.5:3b roda na propria máquina da dupla (8 GB de RAM),
    respeitando a regra de custo zero da especificacao.
    """
    return LLM(
        model=f"ollama/{OLLAMA_MODEL}",
        base_url=OLLAMA_BASE_URL,
        timeout=OLLAMA_TIMEOUT_SEGUNDOS,
    )
