"""Roteiro pedagogico real, com respostas integrais e rubricas explicitas.

Preserva evidencias/testes_etapa7; novas execucoes usam evidencias/execucoes.
"""
import sys


def main():
    from executar_testes import main as executar
    return executar(["--modo", "pedagogico", *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
