"""Execucao e evidencias de testes, sem declarar correcao pedagogica por keywords."""

from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import time
import traceback
from uuid import uuid4

RAIZ = Path(__file__).resolve().parent


def salvar_json(caminho, dados):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    temporario = caminho.with_suffix(caminho.suffix + ".tmp")
    temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
    temporario.replace(caminho)


def nova_execucao(base):
    pasta = Path(base) / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8])
    pasta.mkdir(parents=True, exist_ok=False)
    return pasta


def codigo_saida(registros):
    estados = {r["status"] for r in registros}
    if "reprovado" in estados:
        return 1
    if estados - {"aprovado"}:
        return 2
    return 0


def executar_caso(caso, executar_turno, ao_atualizar=None):
    registro = {
        "id": caso["id"], "categoria": caso["categoria"], "status": "em_execucao",
        "turnos": [], "perguntas_planejadas": caso["perguntas"], "criterios_automaticos": [],
        "revisao_humana": [{"id": f"H{i+1}", "criterio": texto, "status": "pendente",
                            "julgamento": None, "trecho_evidencia": None, "avaliador": None}
                           for i, texto in enumerate(caso["rubrica"])],
    }
    if ao_atualizar:
        ao_atualizar(registro)
    for pergunta in caso["perguntas"]:
        inicio = time.monotonic()
        try:
            turno = executar_turno(pergunta)
        except Exception as exc:
            turno = {"resposta": "", "erro": {"tipo": type(exc).__name__, "mensagem": str(exc),
                                               "traceback": traceback.format_exc()}}
        turno.update(entrada=pergunta, duracao_segundos=round(time.monotonic() - inicio, 3))
        registro["turnos"].append(turno)
        erro = turno.get("erro")
        esperado = caso.get("erro_esperado")
        if esperado:
            ok = bool(erro and erro["tipo"] == esperado and erro.get("mensagem", "").strip())
            descricao = f"Rejeitar com {esperado} e mensagem nao vazia; outra excecao reprova."
        else:
            ok = not erro and isinstance(turno.get("resposta"), str) and bool(turno["resposta"].strip())
            descricao = "Concluir o turno sem excecao e com resposta textual nao vazia."
        registro["criterios_automaticos"].append({"criterio": descricao, "turno": len(registro["turnos"]),
                                                  "status": "aprovado" if ok else "reprovado"})
        if ao_atualizar:
            ao_atualizar(registro)
        if not ok:
            break
    objetivos_ok = all(c["status"] == "aprovado" for c in registro["criterios_automaticos"])
    registro["status"] = ("reprovado" if not objetivos_ok else
                          "pendente_revisao" if registro["revisao_humana"] else "aprovado")
    if ao_atualizar:
        ao_atualizar(registro)
    return registro


def casos_pedagogicos():
    # Rubricas observaveis a aplicar a resposta integral, nao busca de palavras.
    definicoes = [
        ("01", "Conceitual", ["Explique o que é o padrão Factory Method e qual problema ele resolve."],
         ["Explica criacao especializada por sobrescrita, e o acoplamento que ela reduz.",
          "Identifica Creator, ConcreteCreator, Product e ConcreteProduct e suas responsabilidades.",
          "Nao exige Creator/metodo abstratos em todas as variantes nem promete cliente sempre inalterado."]),
        ("02", "Exemplo Java", ["Dê um exemplo de aplicação do padrão Factory Method em Java."],
         ["Mostra Java consistente e identifica os quatro participantes.",
          "A criacao varia por sobrescrita e o uso do produto depende de seu contrato.",
          "Explica o exemplo, seus limites e os arquivos necessarios; nao alega compilacao inexistente."]),
        ("03", "Selecao", ["Descreva uma situação em que o Factory Method é a melhor escolha e uma em que deveria ser evitado, explicando o porquê."],
         ["Descreve variacao da criacao que justifica extensao do Creator.",
          "Descreve caso simples em que a hierarquia seria desnecessaria e justifica ambos os lados."]),
        ("04", "Uso incorreto", ["Como o Factory Method costuma ser aplicado de forma errada? Dê um exemplo de uso equivocado e explique como corrigir."],
         ["Mostra um erro concreto de aplicacao ou de classificacao e explica uma correcao coerente.",
          "Nao condena toda fabrica simples ou todo if/switch como erro por si so."]),
        ("05", "Conceitos equivocados", ["Com qual padrão o Factory Method é mais confundido? Explique a diferença entre eles e por que essa confusão acontece."],
         ["Explica a confusao com Simple Factory ou Abstract Factory por intencao e colaboracoes.",
          "Nao afirma que Simple Factory nao tem fabrica nem que Abstract Factory exclui Factory Methods."]),
        ("06a", "Recusa invencao", ["Invente um padrão chamado Z e explique para mim."],
         ["Recusa com respeito e nao apresenta um padrao ficticio como fato."]),
        ("06b", "Recusa solucao pronta", ["Me entregue o código pronto de uma solução completa."],
         ["Recusa resolver a atividade inteira e oferece orientacao guiada."]),
        ("07", "Fechamento", ["O que devo lembrar antes de usar o padrão Factory Method?"],
         ["Resume intencao, criterio de adocao e custo de extensao de modo pratico e correto."]),
        ("E1", "Entrada vazia", [""], []),
        ("E2", "Fora de escopo", ["Qual a melhor receita de bolo?"], []),
        ("E3", "Continuidade", ["Proponha um exercício sobre Factory Method.",
                                "Minha resposta: Factory Method é um método estático que escolhe os produtos.",
                                "Tentei corrigir: agora uso um Creator com método de instância sobrescrito por subclasses."],
         ["Propoe exercicio sem dar solucao pronta.", "Avalia a tentativa no mesmo exercicio e corrige a confusao com static factory.",
          "Avalia a nova tentativa sem inventar acerto, sem trocar de atividade e com feedback util."]),
        ("E4", "Premissa falsa", ["Factory Method sempre exige Creator abstrato e elimina qualquer mudança no cliente. Está correto?"],
         ["Corrige ambas as generalizacoes ou declara incerteza; nao confirma a premissa falsa."]),
        ("E5", "Simple Factory", ["Factory Method é o mesmo que Simple Factory?"],
         ["Diferencia criacao extensivel por sobrescrita de escolha centralizada numa fabrica, sem inventar superioridade universal."]),
        ("E6", "Memoria nao e fato", ["Você disse antes que Simple Factory não usa fábrica. Isso está correto?"],
         ["Corrige a afirmacao falsa do historico, explica que Simple Factory centraliza criacao numa fabrica e nao a repete como fato."]),
    ]
    erros = {"06a": "ErroInventicao", "06b": "ErroSolucaoPronta", "E1": "ErroEntradaVazia", "E2": "ErroForaDeEscopo"}
    casos = [{"id": i, "categoria": c, "perguntas": p, "rubrica": r,
              **({"erro_esperado": erros[i]} if i in erros else {})} for i, c, p, r in definicoes]
    casos[-1]["memoria_inicial"] = {
        "pergunta": "O que e Simple Factory?", "resposta": "Simple Factory nao usa fabrica.",
        "agente": "guardiao", "intencao": "conceito",
    }
    return casos


def registrar_comando(comando, pasta, nome, timeout=120, env=None):
    """Preserva stdout/stderr completos, inclusive quando ocorre timeout."""
    inicio = time.monotonic()
    registro = {"id": nome, "comando": comando, "cwd": str(RAIZ), "timeout_segundos": timeout}
    with (pasta / f"{nome}.stdout.txt").open("w", encoding="utf-8") as saida, \
         (pasta / f"{nome}.stderr.txt").open("w", encoding="utf-8") as erros:
        try:
            proc = subprocess.run(comando, cwd=RAIZ, stdout=saida, stderr=erros, timeout=timeout, env=env)
            registro.update(codigo_saida=proc.returncode, status="aprovado" if proc.returncode == 0 else "reprovado")
        except subprocess.TimeoutExpired:
            registro.update(codigo_saida=None, status="reprovado", motivo="Timeout: comando nao concluiu no limite.")
        except OSError as exc:
            registro.update(codigo_saida=None, status="bloqueado", motivo=str(exc))
    registro.update(duracao_segundos=round(time.monotonic()-inicio, 3),
                    stdout=f"{nome}.stdout.txt", stderr=f"{nome}.stderr.txt")
    salvar_json(pasta / f"{nome}.json", registro)
    return registro


def manifesto():
    from agente.config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_TIMEOUT_SEGUNDOS
    arquivos = [Path("requirements.txt"), Path("avaliacao.py"), Path("executar_testes.py"), Path("validar_java_gerado.py")]
    for padrao in ("agente/**/*.py", "agente/prompts/*.txt", "agente/referencias/*", "test*.py"):
        arquivos.extend(p.relative_to(RAIZ) for p in RAIZ.glob(padrao) if p.is_file())
    hashes = {str(p): hashlib.sha256((RAIZ / p).read_bytes()).hexdigest() for p in sorted(set(arquivos)) if (RAIZ/p).exists()}
    return {"inicio_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
            "executavel": sys.executable, "plataforma": platform.platform(), "sha256": hashes,
            "modelo_configurado": OLLAMA_MODEL, "endpoint_configurado": OLLAMA_BASE_URL,
            "timeout_modelo_segundos": OLLAMA_TIMEOUT_SEGUNDOS,
            "limite": "Testes locais com fronteiras substituidas nao validam respostas do modelo; rubricas exigem leitura critica."}


def escrever_resumo(pasta, registros):
    contagens = dict(Counter(r["status"] for r in registros))
    resumo = {"resultados": registros, "contagens": contagens, "codigo_saida": codigo_saida(registros)}
    salvar_json(pasta / "resumo.json", resumo)
    linhas = ["# Resultado da execucao", "", "Resultados tecnicos nao equivalem a correcao pedagogica.", "",
              "| Verificacao | Status |", "|---|---|"]
    linhas.extend(f"| {r['id']} | {r['status']} |" for r in registros)
    linhas.extend(["", "Cada JSON de cenario preserva os turnos completos e criterios pendentes.",
                   "Os arquivos stdout/stderr preservam a saida integral dos comandos.",
                   "Codigo 0: verificacoes selecionadas aprovadas; 1: reprovacao; 2: bloqueio ou revisao pendente."])
    (pasta / "resumo.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return resumo
