"""Ponto de entrada: `python -m agente "pergunta aqui"` (contrato obrigatório).

Sem pergunta, abre um laço de conversa no terminal (digite 'sair').
A resposta vai para a saída padrão; mensagens de progresso e tempo vão para a
saída de erro, para não atrapalhar quem automatiza o roteiro de testes.
"""

from __future__ import annotations

import argparse
import sys

from .config import NIVEIS, PADRAO_ENSINADO
from .erro import ErroSistema
from .memoria import MemoriaConversa


def _configurar_terminal() -> None:
    # No Windows, o terminal pode não usar UTF-8 e quebrar acentos.
    for fluxo in (sys.stdout, sys.stderr):
        try:
            fluxo.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass


def _progresso(agentes: list[str]) -> None:
    print(f"[{' → '.join(agentes)}] pensando...", file=sys.stderr, flush=True)


def executar_uma_vez(pergunta: str, sessao_id: str = "default", nivel: str = "", mostrar_progresso: bool = True) -> int:
    """Executa uma pergunta e imprime a resposta. Retorna o código de saída."""
    from .fluxo import executar_fluxo  # adia o import do CrewAI até ser necessário

    try:
        resultado = executar_fluxo(
            pergunta, sessao_id=sessao_id, nivel=nivel,
            ao_iniciar=_progresso if mostrar_progresso else None,
        )
    except ErroSistema as erro:
        print(f"\n[Erro] {erro.mensagem_usuario}")
        if erro.mensagem_tecnica:
            print(f"[Detalhe técnico] {erro.mensagem_tecnica}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nInterrompido.")
        return 130
    except Exception as erro:  # última proteção: nunca mostrar traceback ao estudante
        print(f"\n[Erro] Ocorreu um erro inesperado: {erro}")
        print("Tente novamente ou verifique se o Ollama está rodando.")
        return 1
    print(f"\nSistema ({PADRAO_ENSINADO}):\n{resultado.resposta}\n")
    if mostrar_progresso and resultado.tipo == "resposta":
        print(f"(respondido em {resultado.duracao_segundos:.0f} s)", file=sys.stderr)
    return 0


def modo_interativo(sessao_id: str = "interativo", nivel: str = "") -> int:
    """Laço de conversa contínua no terminal."""
    print(f"\nSistema pedagógico: padrão {PADRAO_ENSINADO}.")
    print(f"Sessão: {sessao_id}")
    print("Digite 'sair' para encerrar.\n")
    while True:
        try:
            pergunta = input("Você: ")
        except (EOFError, KeyboardInterrupt):
            print("\nEncerrando.")
            return 0
        if pergunta.strip().lower() in {"sair", "exit", "quit"}:
            print("Encerrando.")
            return 0
        if not pergunta.strip():
            print("Digite uma pergunta.\n")
            continue
        executar_uma_vez(pergunta, sessao_id=sessao_id, nivel=nivel)


def main() -> int:
    _configurar_terminal()
    parser = argparse.ArgumentParser(description=f"Chat pedagógico: {PADRAO_ENSINADO}")
    parser.add_argument("--sessao", metavar="ID", help="identificador para iniciar ou retomar uma conversa")
    parser.add_argument("--limpar-sessao", action="store_true", help="apaga o histórico e o exercício da sessão")
    parser.add_argument("--nivel", choices=NIVEIS, help="nível do estudante (ajusta a linguagem e os exemplos)")
    parser.add_argument("--silencioso", action="store_true", help="não mostra progresso nem tempo")
    parser.add_argument("pergunta", nargs="*", help="pergunta; sem ela, abre o modo interativo")
    args = parser.parse_args()
    sessao_id = args.sessao or ("default" if args.pergunta or args.limpar_sessao else "interativo")
    try:
        memoria = MemoriaConversa(sessao_id)
        if args.limpar_sessao:
            memoria.limpar()
            print(f"Sessão '{sessao_id}' limpa.")
    except (ValueError, OSError) as exc:
        parser.error(str(exc))

    if args.pergunta:
        return executar_uma_vez(
            " ".join(args.pergunta), sessao_id=sessao_id, nivel=args.nivel or "",
            mostrar_progresso=not args.silencioso,
        )
    if args.limpar_sessao:
        return 0
    return modo_interativo(sessao_id=sessao_id, nivel=args.nivel or "")


if __name__ == "__main__":
    raise SystemExit(main())
