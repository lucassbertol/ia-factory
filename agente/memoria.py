"""Gerenciamento da memoria da conversa.

A memoria eh persistida em arquivos JSON, um por sessao, para que o dialogo
permaneça coerente entre turnos mesmo quando a CLI encerra apos cada comando
(`python -m agente "pergunta"`).

Memoria != conhecimento factual: informacoes ditas pelo modelo em turnos
anteriores nao sao tratadas automaticamente como verdade; o Guardião
reavalia a confiabilidade a cada turno.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .config import MEMORIA_DIR, MAX_CONTEXTO_CARACTERES


class MemoriaConversa:
    """Carrega e salva o historico de turnos de uma sessao."""

    def __init__(self, sessao_id: str) -> None:
        self.sessao_id = sessao_id
        self.caminho = MEMORIA_DIR / f"{sessao_id}.json"
        MEMORIA_DIR.mkdir(parents=True, exist_ok=True)
        self._historico: list[dict[str, Any]] = self._carregar()

    def _carregar(self) -> list[dict[str, Any]]:
        if not self.caminho.exists():
            return []
        try:
            with self.caminho.open("r", encoding="utf-8") as f:
                dados = json.load(f)
            return dados if isinstance(dados, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def salvar_turno(
        self,
        pergunta: str,
        resposta: str,
        agente: str,
    ) -> None:
        """Adiciona um turno ao historico e persiste em disco."""
        turno = {
            "timestamp": datetime.now().isoformat(),
            "pergunta": pergunta,
            "resposta": resposta,
            "agente": agente,
        }
        self._historico.append(turno)
        self._persistir()

    def _persistir(self) -> None:
        tmp = self.caminho.with_suffix(".json.tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(self._historico, f, ensure_ascii=False, indent=2)
        tmp.replace(self.caminho)

    def contexto_texto(self) -> str:
        """Retorna o historico recente como texto para injeção nos prompts.

        So os ultimos turnos sao usados, respeitando MAX_CONTEXTO_CARACTERES,
        para evitar exceder o limite de contexto do modelo local.
        """
        if not self._historico:
            return ""
        partes: list[str] = []
        total = 0
        for turno in reversed(self._historico):
            bloco = (
                f"[{turno['timestamp']}] Estudante: {turno['pergunta']}\n"
                f"[{turno['timestamp']}] Sistema ({turno['agente']}): {turno['resposta']}\n"
            )
            if total + len(bloco) > MAX_CONTEXTO_CARACTERES and partes:
                break
            partes.insert(0, bloco)
            total += len(bloco)
        if not partes:
            return ""
        return "=== Historico da conversa (sessao " + self.sessao_id + ") ===\n" + "".join(partes)

    def limpar(self) -> None:
        """Remove o historico da sessao (uso em testes/debug)."""
        self._historico = []
        if self.caminho.exists():
            self.caminho.unlink()
