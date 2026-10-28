"""Carregamento dos prompts de sistema dos agentes.

Os arquivos de prompt ficam em `agente/prompts/*.txt` e sao carregados
dinamicamente aqui, de modo que a documentacao (Etapa 8) esteja sempre
sincronizada com a implementacao.
"""

from __future__ import annotations

from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent


def carregar_prompt(nome_agente: str) -> str:
    """Retorna o conteudo do prompt de sistema do agente informado.

    Args:
        nome_agente: um de 'tutor', 'exemplificador', 'inquiridor', 'guardiao'.

    Raises:
        FileNotFoundError: se o arquivo do prompt nao existir.
        ValueError: se o nome do agente for invalido.
    """
    validos = {"tutor", "exemplificador", "inquiridor", "guardiao"}
    if nome_agente not in validos:
        raise ValueError(f"Agente invalido: {nome_agente}. Validos: {sorted(validos)}")
    caminho = PROMPTS_DIR / f"{nome_agente}.txt"
    if not caminho.exists():
        raise FileNotFoundError(f"Prompt nao encontrado: {caminho}")
    return caminho.read_text(encoding="utf-8")
