"""Testes reais de continuidade e correcao de historico falso.

Preserva todos os turnos e snapshots da memoria, sem aprovar so por salva-los.
"""
import sys


def main():
    from executar_testes import main as executar
    return executar(["--modo", "pedagogico", "--casos", "E3,E6", *sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())
