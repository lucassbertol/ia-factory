"""Tratamento centralizado de erros do sistema.

Cobre: entrada vazia, falha do Ollama/modelo, saida inesperada,
perguntas fora de escopo e pedidos de solucao pronta.
Todas as classes herdam de Exception para poderem ser capturadas.
"""

from __future__ import annotations


class ErroSistema(Exception):
    """Exceção base com mensagem amigável ao estudante e detalhe técnico opcional."""

    def __init__(
        self,
        codigo: str,
        mensagem_usuario: str,
        mensagem_tecnica: str | None = None,
    ) -> None:
        super().__init__(mensagem_usuario)
        self.codigo = codigo
        self.mensagem_usuario = mensagem_usuario
        self.mensagem_tecnica = mensagem_tecnica


class ErroEntradaVazia(ErroSistema):
    def __init__(self) -> None:
        super().__init__(
            codigo="ENTRADA_VAZIA",
            mensagem_usuario=(
                "Voce nao digitou nenhuma pergunta. "
                "Tente novamente, por exemplo: "
                '"python -m agente "O que e o padrao Factory Method?"'
            ),
        )


class ErroModeloIndisponivel(ErroSistema):
    def __init__(self, detalhe: str) -> None:
        super().__init__(
            codigo="MODELO_INDISPONIVEL",
            mensagem_usuario=(
                "Nao foi possivel comunicar com o modelo local (Ollama). "
                "Verifique se o Ollama esta rodando e se o modelo qwen2.5:3b "
                "foi baixado. Detalhe: " + detalhe
            ),
            mensagem_tecnica=detalhe,
        )


class ErroSaidaInesperada(ErroSistema):
    def __init__(self, detalhe: str) -> None:
        super().__init__(
            codigo="SAIDA_INESPERADA",
            mensagem_usuario=(
                "O modelo retornou uma saida inesperada e nao foi possivel "
                "montar uma resposta confiavel. Tente reformular sua pergunta."
            ),
            mensagem_tecnica=detalhe,
        )


class ErroForaDeEscopo(ErroSistema):
    def __init__(self, topico: str) -> None:
        super().__init__(
            codigo="FORA_DE_ESCOPO",
            mensagem_usuario=(
                f"Este sistema ensina apenas o padrao Factory Method. "
                f"'{topico}' esta fora do escopo. Consulte o material da disciplina."
            ),
        )


class ErroSolucaoPronta(ErroSistema):
    """Recusa educada a pedido de solucao completa pronta."""

    def __init__(self) -> None:
        super().__init__(
            codigo="SOLUCAO_PRONTA_RECUSADA",
            mensagem_usuario=(
                "Nao entrego solucoes prontas, pois isso prejudica seu aprendizado. "
                "Posso orientar voce passo a passo: qual parte voce gostaria de "
                "entender primeiro?"
            ),
        )


class ErroInventicao(ErroSistema):
    """Recusa educada a pedido de inventacao de fato/padrao."""

    def __init__(self) -> None:
        super().__init__(
            codigo="INVENTICAO_RECUSADA",
            mensagem_usuario=(
                "Nao posso inventar padroes, participantes, consequencias ou exemplos. "
                "Quando nao sei algo, digo que nao sei e sugiro a consulta ao material da disciplina."
            ),
        )
