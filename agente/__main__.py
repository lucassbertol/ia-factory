"""Ponto de entrada do pacote: `python -m agente`.

Interface padronizada exigida pelo PDF:
    python -m agente "pergunta aqui"

Processa o texto, chama o sistema multiagente, imprime a resposta e encerra.
Também oferece um modo interativo contínuo no terminal (sair para encerrar).

Tratamento de erros:
  - Entrada vazia
  - Falha do Ollama / modelo
  - Saída inesperada
  - Recusa educada a invenção e solução pronta
"""

from __future__ import annotations

import sys

from .config import CLI_COMANDO, PADRAO_ENSINADO
from .erro import (
    ErroEntradaVazia,
    ErroForaDeEscopo,
    ErroInventicao,
    ErroModeloIndisponivel,
    ErroSaidaInesperada,
    ErroSolucaoPronta,
)
from .fluxo import executar_fluxo


def _imprimir_erro(erro) -> None:
    """Imprime uma mensagem de erro amigável ao estudante."""
    print(f"\n[Erro] {erro.mensagem_usuario}")
    if erro.mensagem_tecnica:
        print(f"[Detalhe tecnico] {erro.mensagem_tecnica}")


def executar_uma_vez(pergunta: str) -> int:
    """Executa uma única pergunta e imprime a resposta. Retorna código de saída."""
    try:
        resultado = executar_fluxo(pergunta)
        print(f"\nSistema ({PADRAO_ENSINADO}):\n{resultado.resposta}\n")
        return 0
    except ErroEntradaVazia as e:
        _imprimir_erro(e)
        return 1
    except ErroInventicao as e:
        _imprimir_erro(e)
        return 1
    except ErroSolucaoPronta as e:
        _imprimir_erro(e)
        return 1
    except ErroForaDeEscopo as e:
        _imprimir_erro(e)
        return 1
    except ErroModeloIndisponivel as e:
        _imprimir_erro(e)
        return 1
    except ErroSaidaInesperada as e:
        _imprimir_erro(e)
        return 1
    except Exception as e:  # falha inesperada não tratada
        print(f"\n[Erro] Ocorreu um erro inesperado: {e}")
        print("Tente novamente ou verifique se o Ollama está rodando.")
        return 1


def modo_interativo() -> int:
    """Abre um laço de conversa contínua no terminal."""
    print(f"\nSistema pedagógico: padrão {PADRAO_ENSINADO}.")
    print("Digite 'sair' para encerrar.\n")
    sessao_id = "interativo"
    while True:
        try:
            pergunta = input("Você: ")
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando.")
            return 0
        if pergunta.strip().lower() == "sair":
            print("Encerrando.")
            return 0
        if not pergunta.strip():
            print("Digite uma pergunta válida.\n")
            continue
        codigo = executar_uma_vez(pergunta)
        if codigo != 0:
            print("(Tente novamente.)\n")


def main() -> int:
    """Ponto de entrada principal da CLI."""
    args = sys.argv[1:]

    if not args:
        # Nenhum argumento: modo interativo
        return modo_interativo()

    pergunta = " ".join(args)
    return executar_uma_vez(pergunta)


if __name__ == "__main__":
    raise SystemExit(main())
