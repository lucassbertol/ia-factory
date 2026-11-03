"""Compila um exemplo Java extraido da resposta integral; nunca o executa."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from avaliacao import salvar_json


def compilar_resposta(resposta, pasta):
    pasta = Path(pasta)
    pasta.mkdir(parents=True, exist_ok=True)
    blocos = re.findall(r"```java\s*\n(.*?)```", resposta, flags=re.S | re.I)
    resultado = {"status": "pendente_revisao", "codigo_executado": False,
                 "limite": "Compilacao verifica sintaxe e tipos, nao correcao do padrao.",
                 "blocos_java_integrais": blocos}
    if not blocos:
        resultado.update(status="reprovado", motivo="Resposta ao pedido de exemplo nao contem bloco Java identificado.")
    elif not shutil.which("javac"):
        resultado.update(status="bloqueado", motivo="Compilador javac nao disponivel.")
    elif len(blocos) != 1:
        resultado["motivo"] = "Varios blocos/trechos: conferir organizacao dos arquivos antes de compilar; nao concatenar nem alterar a resposta."
    else:
        publicos = re.findall(r"\bpublic\s+(?:(?:abstract|final)\s+)?(?:class|interface|enum)\s+([A-Za-z_$][\w$]*)", blocos[0])
        if len(set(publicos)) != 1:
            resultado["motivo"] = "Nao foi possivel determinar um unico arquivo publico; requer revisao dos trechos."
        else:
            arquivo = pasta / f"{publicos[0]}.java"
            arquivo.write_text(blocos[0], encoding="utf-8")
            with tempfile.TemporaryDirectory(prefix="ia-javac-") as classes:
                comando = ["javac", "-proc:none", "-encoding", "UTF-8", "-classpath", classes,
                           "-sourcepath", classes, "-d", classes, str(arquivo.resolve())]
                try:
                    proc = subprocess.run(comando, capture_output=True, text=True, timeout=30)
                    resultado.update(status="aprovado" if proc.returncode == 0 else "reprovado",
                                     compilacao={"comando": comando, "codigo_saida": proc.returncode,
                                                 "stdout": proc.stdout, "stderr": proc.stderr})
                except subprocess.TimeoutExpired as exc:
                    resultado.update(status="reprovado", motivo="Timeout de compilacao.",
                                     compilacao={"comando": comando, "codigo_saida": None,
                                                 "stdout": (exc.stdout or b"").decode() if isinstance(exc.stdout, bytes) else exc.stdout,
                                                 "stderr": (exc.stderr or b"").decode() if isinstance(exc.stderr, bytes) else exc.stderr})
    salvar_json(pasta / "compilacao.json", resultado)
    return resultado


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidencia", type=Path)
    parser.add_argument("--saida", required=True, type=Path)
    args = parser.parse_args()
    if (args.saida / "compilacao.json").exists():
        parser.error("A saida ja contem uma compilacao; escolha outra pasta para preservar a evidencia.")
    dados = json.loads(args.evidencia.read_text())
    resultado = compilar_resposta(dados["turnos"][0]["resposta"], args.saida)
    resultado.update(evidencia_original=str(args.evidencia.resolve()),
                     sha256_evidencia=hashlib.sha256(args.evidencia.read_bytes()).hexdigest())
    salvar_json(args.saida / "compilacao.json", resultado)
    print(f"Compilacao: {resultado['status']}. Evidencias: {args.saida}")
    return 0 if resultado["status"] == "aprovado" else 1 if resultado["status"] == "reprovado" else 2


if __name__ == "__main__":
    raise SystemExit(main())
