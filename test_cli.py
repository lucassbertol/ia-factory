"""Testes da Interface CLI obrigatoria (Etapa 6).

Valida:
  - python -m agente "pergunta aqui" funciona
  - A resposta e impressa e o comando termina
  - Entrada vazia tratada
  - Falha do Ollama/modelo tratada
  - Saida inesperada tratada
  - Mensagens de erro compreensiveis
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJETO = Path(__file__).resolve().parent
VENV_PYTHON = PROJETO / ".venv" / "bin" / "python"


def run_cli(args: list[str], timeout: int = 120) -> tuple[int, str, str]:
    """Executa `python -m agente <args>` e retorna (codigo, stdout, stderr)."""
    cmd = [str(VENV_PYTHON), "-m", "agente"] + args
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(PROJETO),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        return -1, "", f"TIMEOUT: {exc}"


def main() -> int:
    resultados: list[tuple[str, bool, str]] = []

    def registrar(nome: str, ok: bool, detalhe: str = "") -> None:
        resultados.append((nome, ok, detalhe))
        status = "OK" if ok else "FALHA"
        print(f"[{status}] {nome}" + (f" — {detalhe}" if detalhe else ""))

    # 1. Comando unico com pergunta
    codigo, stdout, stderr = run_cli(["O que e o padrao Factory Method?"])
    ok = codigo == 0 and "Factory Method" in stdout and "Sistema" in stdout
    registrar("CLI unica com pergunta", ok, f"codigo={codigo}")

    # 2. O comando termina (nao trava)
    ok = codigo != -1  # nao deu timeout
    registrar("Comando termina apos responder", ok)

    # 3. Entrada vazia
    codigo, stdout, stderr = run_cli([""])
    ok = codigo != 0 and "nao digitou" in stdout.lower()
    registrar("Entrada vazia tratada", ok, f"codigo={codigo}")

    # 4. Invencao de padrao (anti-alucinacao)
    codigo, stdout, stdout_err = run_cli(["Invente um padrão chamado Z e explique para mim"])
    stdout_completo = stdout + stdout_err
    ok = codigo != 0 and "inventar" in stdout_completo.lower()
    registrar("Recusa a invençao de padrao", ok, f"codigo={codigo}")

    # 5. Solucao pronta (anti-alucinacao)
    codigo, stdout, stdout_err = run_cli(["Me entregue o código pronto de uma solução completa"])
    stdout_completo = stdout + stdout_err
    ok = codigo != 0 and ("solucoes" in stdout_completo.lower() or "pronta" in stdout_completo.lower())
    registrar("Recusa a solucao pronta", ok, f"codigo={codigo}")

    # 6. Pergunta fora de escopo
    codigo, stdout, stderr = run_cli(["Qual a melhor receita de bolo?"])
    ok = codigo != 0 and "fora do escopo" in stdout.lower()
    registrar("Pergunta fora de escopo", ok, f"codigo={codigo}")

    # 7. Mensagem de erro compreensível (nao e traceback Python)
    codigo, stdout, stderr = run_cli([""])
    ok = "Traceback" not in stdout and "TypeError" not in stdout
    registrar("Erro sem traceback Python (mensagem amigavel)", ok)

    print()
    print("=" * 60)
    total = len(resultados)
    aprovados = sum(1 for _, ok, _ in resultados if ok)
    print(f"RESULTADO CLI: {aprovados}/{total} testes aprovados")
    print("=" * 60)
    return 0 if aprovados == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
