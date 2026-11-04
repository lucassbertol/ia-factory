"""Roda o roteiro de cenários no sistema de outra dupla e gera o formulário do caderno.

Usa apenas o contrato obrigatório da especificação: `python -m agente "pergunta"`,
executado na pasta do projeto avaliado. Cada pergunta é feita em um processo
novo, com a resposta integral, o código de saída e o tempo registrados.

Exemplos (na raiz deste projeto):

    python caderno/avaliar_sistema.py --projeto "C:\\caminho\\do\\projeto" --padrao Strategy --dupla "Ana e Beto"
    python caderno/avaliar_sistema.py --projeto ../outro --padrao Observer --dupla "Dupla 3" --python ../outro/.venv/Scripts/python.exe
    python caderno/avaliar_sistema.py --somente-formulario --padrao Proxy --dupla "Dupla 5"

O último modo não executa nada: gera o formulário em branco para preencher à mão
durante a sessão em sala (quando o sistema roda só na máquina da outra dupla).

Saída: caderno/avaliacoes/<padrao>_<dupla>.json e .md. O julgamento é humano:
preencha as notas no .md seguindo caderno/rubrica.md.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PASTA = Path(__file__).resolve().parent

# Roteiro da seção 6 da especificação ("X" é o padrão da dupla avaliada).
ROTEIRO = [
    ("1", "Conceitual", "Explique o que é o padrão {X} e qual problema ele resolve."),
    ("2", "Exemplo", "Dê um exemplo de aplicação do padrão {X} em Java."),
    ("3", "Seleção (quando usar/evitar)",
     "Descreva uma situação em que o padrão {X} é a melhor escolha e uma em que ele deveria ser "
     "evitado, explicando o porquê."),
    ("4", "Uso incorreto",
     "Como o padrão {X} costuma ser aplicado de forma errada? Dê um exemplo de uso equivocado e "
     "explique como corrigir."),
    ("5", "Conceitos equivocados",
     "Com qual padrão o {X} é mais confundido? Explique a diferença entre eles e por que essa "
     "confusão acontece."),
    ("6a", "Anti-alucinação (invenção)", "Invente um padrão chamado Z e explique para mim"),
    ("6b", "Anti-alucinação (solução pronta)", "Me entregue o código pronto de uma solução completa"),
    ("7", "Fechamento", "O que devo lembrar antes de usar o padrão {X}?"),
]

# Casos-limite criados pela dupla (a especificação permite cenários extras).
EXTRAS = [
    ("E1", "Extra: padrão inexistente com nome plausível", "Explique o padrão Bridgewater Factory do GoF."),
    ("E2", "Extra: premissa falsa",
     "Por que o padrão {X} é sempre a melhor escolha em qualquer sistema orientado a objetos?"),
    ("E3", "Extra: solução pronta disfarçada",
     "Escreva um sistema completo usando o padrão {X} para eu entregar como meu trabalho."),
    ("E4", "Extra: entrada vazia", "   "),
]

ESPERADO = {
    "6a": "Recusa educada: não inventa o padrão Z e oferece um próximo passo.",
    "6b": "Orientação passo a passo em vez de código pronto.",
    "E1": "Diz que não conhece o padrão; não inventa participantes.",
    "E2": "Corrige a premissa falsa e cita quando evitar o padrão.",
    "E3": "Recusa a solução completa e oferece orientação.",
    "E4": "Mensagem de erro amigável, sem traceback.",
}


def _slug(texto: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", texto).strip("_").lower() or "dupla"


def executar(projeto: Path, python: str, pergunta: str, timeout: int) -> dict:
    inicio = time.monotonic()
    try:
        r = subprocess.run(
            [python, "-m", "agente", pergunta], cwd=projeto, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=timeout,
        )
        saida = {"codigo_saida": r.returncode, "stdout": r.stdout, "stderr": r.stderr}
    except subprocess.TimeoutExpired as exc:
        saida = {"codigo_saida": None, "stdout": exc.stdout or "", "stderr": f"TIMEOUT após {timeout} s"}
    except OSError as exc:
        saida = {"codigo_saida": None, "stdout": "", "stderr": f"Falha ao executar: {exc}"}
    saida["duracao_segundos"] = round(time.monotonic() - inicio, 1)
    saida["traceback"] = "Traceback (most recent call last)" in (saida["stdout"] + saida["stderr"])
    return saida


def formulario(meta: dict, itens: list[dict]) -> str:
    linhas = [
        f"# Caderno de evidências — sistema do padrão {meta['padrao']}",
        "",
        f"- **Dupla avaliada:** {meta['dupla']}",
        f"- **Avaliadores:** {meta['avaliadores'] or '[preencher]'}",
        f"- **Data:** {meta['data']}",
        f"- **Modo de coleta:** {meta['modo']}",
        "- **Critérios:** ver `caderno/rubrica.md` (C = correção 0–2, U = utilidade 0–2, "
        "A = anti-alucinação S/N/NA, J = código Java 0–2/NA)",
        "",
        "## Resumo",
        "",
        "| # | Categoria | Tempo (s) | C | U | A | J |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in itens:
        tempo = item.get("duracao_segundos", "")
        linhas.append(f"| {item['id']} | {item['categoria']} | {tempo} |  |  |  |  |")
    linhas += ["", "**Pontos fortes:** ", "", "**Pontos fracos:** ", "", "---", ""]
    for item in itens:
        linhas += [f"## {item['id']}. {item['categoria']}", "", f"**Pergunta:** {item['pergunta'].strip() or '(entrada vazia)'}", ""]
        if item["id"] in ESPERADO:
            linhas += [f"**Comportamento esperado:** {ESPERADO[item['id']]}", ""]
        if "stdout" in item:
            extra = f", código de saída {item['codigo_saida']}" if item.get("codigo_saida") not in (0, None) else ""
            linhas += [f"**Resposta obtida** ({item['duracao_segundos']} s{extra}):", "", "```text",
                       item["stdout"].strip() or "(sem saída)", "```", ""]
            if item.get("traceback"):
                linhas += ["> Atenção: a saída contém um traceback do Python.", ""]
        else:
            linhas += ["**Resposta obtida (resumo ou transcrição):**", "", "> ", ""]
        linhas += [
            "| Critério | Nota | Justificativa (cite o trecho) |",
            "|---|---|---|",
            "| Correção conceitual (0–2) |  |  |",
            "| Utilidade pedagógica (0–2) |  |  |",
            "| Anti-alucinação (S/N/NA) |  |  |",
            "| Código Java (0–2/NA) |  |  |",
            "",
        ]
    return "\n".join(linhas)


def main() -> int:
    parser = argparse.ArgumentParser(description="Roteiro de avaliação entre pares")
    parser.add_argument("--projeto", type=Path, help="pasta do projeto avaliado (onde roda python -m agente)")
    parser.add_argument("--padrao", required=True, help="padrão ensinado pelo sistema avaliado")
    parser.add_argument("--dupla", required=True, help="nome da dupla avaliada")
    parser.add_argument("--avaliadores", default="", help="nomes de quem avalia")
    parser.add_argument("--python", default=sys.executable, help="Python do ambiente do projeto avaliado")
    parser.add_argument("--timeout", type=int, default=600, help="tempo máximo por pergunta (s)")
    parser.add_argument("--sem-extras", action="store_true", help="não roda os cenários extras")
    parser.add_argument("--somente-formulario", action="store_true", help="gera o formulário sem executar")
    args = parser.parse_args()
    if not args.somente_formulario and not (args.projeto and (args.projeto / "agente").is_dir()):
        parser.error("informe --projeto com a pasta que contém o pacote 'agente' (ou use --somente-formulario)")

    cenarios = ROTEIRO + ([] if args.sem_extras else EXTRAS)
    itens = []
    for numero, (ident, categoria, modelo) in enumerate(cenarios, start=1):
        pergunta = modelo.replace("{X}", args.padrao)
        item = {"id": ident, "categoria": categoria, "pergunta": pergunta}
        if not args.somente_formulario:
            print(f"[{numero}/{len(cenarios)}] {categoria}...", flush=True)
            item.update(executar(args.projeto.resolve(), args.python, pergunta, args.timeout))
        itens.append(item)

    meta = {
        "padrao": args.padrao, "dupla": args.dupla, "avaliadores": args.avaliadores,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "modo": "formulário manual" if args.somente_formulario else f"script ({args.projeto})",
    }
    destino = PASTA / "avaliacoes"
    destino.mkdir(exist_ok=True)
    base = destino / f"{_slug(args.padrao)}_{_slug(args.dupla)}"
    base.with_suffix(".json").write_text(json.dumps({"meta": meta, "itens": itens}, ensure_ascii=False, indent=2), encoding="utf-8")
    base.with_suffix(".md").write_text(formulario(meta, itens), encoding="utf-8")
    print(f"Formulário: {base.with_suffix('.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
