"""LLM local (Ollama) para os agentes CrewAI.

O CrewAI 1.15 conecta modelos "ollama/..." pelo endpoint compatível com a
OpenAI (/v1/chat/completions), que não permite definir o tamanho da janela de
contexto por requisição. Com a janela padrão do Ollama, o início do prompt
(persona, regras e referência) era cortado em silêncio. Por isso este módulo
implementa um LLM customizado do CrewAI (subclasse de BaseLLM) que chama a API
nativa /api/chat e envia num_ctx, temperatura e limite de tokens em toda chamada.

Tudo roda na própria máquina: nenhuma chave, nuvem ou serviço pago.
"""

from __future__ import annotations

from typing import Any

import httpx
from crewai.llms.base_llm import BaseLLM

from .config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_NUM_CTX,
    OLLAMA_NUM_PREDICT,
    OLLAMA_REPEAT_PENALTY,
    OLLAMA_TEMPERATURA,
    OLLAMA_TIMEOUT_SEGUNDOS,
)


class FalhaOllama(RuntimeError):
    """Falha de comunicação com o servidor Ollama local."""


class OllamaLocal(BaseLLM):
    """Cliente mínimo da API nativa do Ollama, no formato esperado pelo CrewAI."""

    llm_type: str = "ollama_local"
    provider: str = "ollama"
    num_ctx: int = OLLAMA_NUM_CTX
    num_predict: int = OLLAMA_NUM_PREDICT
    timeout: float = OLLAMA_TIMEOUT_SEGUNDOS

    def opcoes(self) -> dict[str, Any]:
        opcoes: dict[str, Any] = {
            "num_ctx": self.num_ctx,
            "num_predict": self.num_predict,
            "temperature": self.temperature,
            # Penaliza repetição: no teste real o modelo entrou em laço repetindo frases.
            "repeat_penalty": OLLAMA_REPEAT_PENALTY,
        }
        if self.stop:
            opcoes["stop"] = list(self.stop)
        return opcoes

    def call(
        self,
        messages,
        tools=None,
        callbacks=None,
        available_functions=None,
        from_task=None,
        from_agent=None,
        response_model=None,
    ) -> str:
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        mensagens = [
            {"role": m.get("role", "user"), "content": str(m.get("content") or "")}
            for m in messages
        ]
        corpo = {
            "model": self.model,
            "messages": mensagens,
            "stream": False,
            "options": self.opcoes(),
        }
        url = f"{(self.base_url or OLLAMA_BASE_URL).rstrip('/')}/api/chat"
        try:
            resposta = httpx.post(url, json=corpo, timeout=self.timeout)
        except httpx.TimeoutException as exc:
            raise FalhaOllama(
                f"Ollama não respondeu em {self.timeout:.0f} s ({url})."
            ) from exc
        except httpx.HTTPError as exc:
            raise FalhaOllama(f"Não foi possível conectar ao Ollama em {url}: {exc}") from exc

        if resposta.status_code == 404:
            raise FalhaOllama(
                f"Modelo '{self.model}' não encontrado no Ollama. "
                f"Execute: ollama pull {self.model}"
            )
        if resposta.status_code >= 400:
            raise FalhaOllama(f"Ollama devolveu HTTP {resposta.status_code}: {resposta.text[:300]}")
        try:
            conteudo = resposta.json()["message"]["content"]
        except (ValueError, KeyError, TypeError) as exc:
            raise FalhaOllama("Resposta do Ollama em formato inesperado.") from exc
        return str(conteudo or "")

    def get_input_tokens_count(self, messages, tools=None, response_model=None) -> int:
        # Mesma estimativa do CrewAI (4 caracteres por token), sem o aviso no terminal.
        if isinstance(messages, str):
            return (len(messages) + 3) // 4
        return (sum(len(str(m.get("content") or "")) for m in messages) + 3) // 4

    def supports_function_calling(self) -> bool:
        return False

    def supports_stop_words(self) -> bool:
        return True

    def get_context_window_size(self) -> int:
        return self.num_ctx


def obter_llm() -> OllamaLocal:
    """LLM configurado para o modelo local (qwen2.5:3b por padrão)."""
    return OllamaLocal(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=OLLAMA_TEMPERATURA,
    )
