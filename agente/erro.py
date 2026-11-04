"""Erros do sistema: entrada vazia, falha do modelo local e saída inesperada.

Recusas (padrão inventado, solução pronta, fora de escopo) não são erros:
são respostas pedagógicas normais, produzidas em agente/recusas.py.
"""

from __future__ import annotations

from .config import OLLAMA_MODEL


class ErroSistema(Exception):
    """Exceção base com mensagem amigável ao estudante e detalhe técnico opcional."""

    def __init__(self, codigo: str, mensagem_usuario: str, mensagem_tecnica: str | None = None) -> None:
        super().__init__(mensagem_usuario)
        self.codigo = codigo
        self.mensagem_usuario = mensagem_usuario
        self.mensagem_tecnica = mensagem_tecnica


class ErroEntradaVazia(ErroSistema):
    def __init__(self) -> None:
        super().__init__(
            codigo="ENTRADA_VAZIA",
            mensagem_usuario=(
                "Você não digitou nenhuma pergunta. Tente, por exemplo: "
                'python -m agente "O que é o padrão Factory Method?"'
            ),
        )


class ErroModeloIndisponivel(ErroSistema):
    def __init__(self, detalhe: str) -> None:
        super().__init__(
            codigo="MODELO_INDISPONIVEL",
            mensagem_usuario=(
                "Não foi possível falar com o modelo local. Verifique se o Ollama está "
                f"aberto (ollama serve) e se o modelo foi baixado (ollama pull {OLLAMA_MODEL})."
            ),
            mensagem_tecnica=detalhe,
        )


class ErroSaidaInesperada(ErroSistema):
    def __init__(self, detalhe: str) -> None:
        super().__init__(
            codigo="SAIDA_INESPERADA",
            mensagem_usuario=(
                "O modelo devolveu uma saída que não consegui transformar em uma resposta "
                "confiável. Tente reformular a pergunta."
            ),
            mensagem_tecnica=detalhe,
        )
