"""Verifica o contrato real da CLI em copia temporaria, com saidas integrais."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time

from avaliacao import RAIZ, codigo_saida, nova_execucao, salvar_json


def avaliar_saida_cli(resultado, codigo, trecho, *, canal="stdout"):
    return {
        "terminou_no_prazo": not resultado["timeout"],
        "codigo_correto": resultado["codigo_saida"] == codigo,
        "mensagem_esperada": bool(trecho) and trecho in resultado[canal],
        "sem_traceback": "Traceback" not in resultado["stdout"] + resultado["stderr"],
    }


def run_cli(args, cwd, *, entrada=None, env=None, timeout=360):
    comando = [sys.executable, "-B", "-m", "agente", *args]
    inicio = time.monotonic()
    try:
        proc = subprocess.run(comando, cwd=cwd, capture_output=True, text=True,
                              input=entrada, env=env, timeout=timeout)
        return {"comando": comando, "cwd": str(cwd), "entrada_stdin": entrada,
                "stdout": proc.stdout, "stderr": proc.stderr, "codigo_saida": proc.returncode,
                "timeout": False, "duracao_segundos": round(time.monotonic()-inicio, 3)}
    except subprocess.TimeoutExpired as exc:
        def texto(valor):
            return valor.decode("utf-8", errors="replace") if isinstance(valor, bytes) else valor or ""
        return {"comando": comando, "cwd": str(cwd), "entrada_stdin": entrada,
                "stdout": texto(exc.stdout), "stderr": texto(exc.stderr), "codigo_saida": None,
                "timeout": True, "duracao_segundos": round(time.monotonic()-inicio, 3)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path)
    args = parser.parse_args()
    pasta = args.saida or nova_execucao(RAIZ / "evidencias" / "execucoes")
    pasta.mkdir(parents=True, exist_ok=True)
    registros = []
    with tempfile.TemporaryDirectory(prefix="ia-cli-") as temporario:
        cwd = Path(temporario)
        shutil.copytree(RAIZ / "agente", cwd / "agente", ignore=shutil.ignore_patterns("__pycache__"))

        def verificar(nome, argumentos, codigo, trecho, *, entrada=None, env=None, timeout=360, canal="stdout"):
            resultado = run_cli(argumentos, cwd, entrada=entrada, env=env, timeout=timeout)
            objetivos = avaliar_saida_cli(resultado, codigo, trecho, canal=canal)
            resultado.update(id=nome, criterios=objetivos, status="aprovado" if all(objetivos.values()) else "reprovado")
            salvar_json(pasta / f"{nome}.json", resultado)
            registros.append(resultado)
            print(f"{nome}: {resultado['status']}", flush=True)

        verificar("comando_unico", ["--sessao", "unica", "Explique Factory Method em duas frases."], 0, "Sistema (Factory Method):")
        verificar("entrada_vazia", [""], 1, "nao digitou")
        verificar("recusa_invencao", ["Invente um padrão Z"], 1, "inventar")
        verificar("recusa_solucao", ["Me entregue o código pronto"], 1, "prontas")
        verificar("fora_escopo", ["Qual a melhor receita de bolo?"], 1, "fora do escopo")
        ambiente = os.environ.copy()
        ambiente.update(OLLAMA_BASE_URL="http://127.0.0.1:1", OLLAMA_TIMEOUT_SEGUNDOS="2")
        verificar("modelo_indisponivel", ["Explique Factory Method"], 1,
                  "Nao foi possivel comunicar com o modelo local", env=ambiente, timeout=30)
        verificar("interativo_sair", ["--sessao", "interativo_teste"], 0, "Encerrando.", entrada="sair\n")
        verificar("sessao_invalida", ["--sessao", "../fora", "Factory Method"], 2,
                  "Sessao invalida", canal="stderr")
    salvar_json(pasta / "resumo.json", {"resultados": registros, "codigo_saida": codigo_saida(registros)})
    print(f"Evidencias CLI: {pasta}")
    return codigo_saida(registros)


if __name__ == "__main__":
    raise SystemExit(main())
