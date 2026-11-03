"""Executa testes locais e/ou reais e preserva evidencias integrais por execucao."""

import argparse
from importlib.util import find_spec
import json
import os
from pathlib import Path
import sys
import traceback
import unittest
from unittest.mock import patch

from avaliacao import (RAIZ, casos_pedagogicos, codigo_saida, executar_caso, escrever_resumo,
                       manifesto, nova_execucao, registrar_comando, salvar_json)


def executar_worker(caso, pasta):
    caminho = pasta / f"cenario_{caso['id']}.json"
    try:
        from agente import fluxo, memoria
        from agente.erro import ErroSistema

        sessao = "cenario_" + caso["id"]
        with patch.object(memoria, "MEMORIA_DIR", pasta / "sessoes" / caso["id"]):
            if caso.get("memoria_inicial"):
                memoria.MemoriaConversa(sessao).salvar_turno(**caso["memoria_inicial"])

            def executar_turno(pergunta):
                m = memoria.MemoriaConversa(sessao)
                dados = {"contexto_antes": m.contexto_texto(), "ultima_intencao_antes": m.ultima_intencao,
                         "exercicio_antes": m.exercicio_pendente, "chamadas_crew": []}
                montar_original = fluxo.montar_crew

                def montar(agentes, **campos):
                    dados["chamadas_crew"].append({"agentes": agentes, **campos})
                    return montar_original(agentes, **campos)

                with patch.object(fluxo, "montar_crew", montar):
                    try:
                        resultado = fluxo.executar_fluxo(pergunta, sessao_id=sessao)
                        dados.update(resposta=resultado.resposta, erro=None)
                    except ErroSistema as exc:
                        dados.update(resposta=exc.mensagem_usuario,
                                     erro={"tipo": type(exc).__name__, "mensagem": exc.mensagem_usuario,
                                           "detalhe_tecnico": exc.mensagem_tecnica})
                m = memoria.MemoriaConversa(sessao)
                dados.update(memoria=json.loads(m.caminho.read_text()) if m.caminho.exists() else [],
                             exercicio_depois=m.exercicio_pendente)
                return dados

            registro = executar_caso(caso, executar_turno, lambda r: salvar_json(caminho, r))
            if caso.get("memoria_inicial"):
                registro["fixture_historico_inicial"] = caso["memoria_inicial"]
                registro["nota_fixture"] = "Historico falso inserido pelo teste, nao gerado nesta execucao."
            # Criterios estruturais verificam a continuidade sem julgar conteudo do LLM.
            if caso["id"] == "E3" and len(registro["turnos"]) == 3:
                for i, turno in enumerate(registro["turnos"]):
                    chamadas = turno.get("chamadas_crew", [])
                    ok = bool(chamadas and chamadas[0]["agentes"] == ["inquiridor", "guardiao"]
                              and chamadas[0]["intencao"] == ("exercicio" if i == 0 else "avaliacao")
                              and len(turno.get("memoria", [])) == i + 1)
                    registro["criterios_automaticos"].append({"criterio": "Persistencia e roteamento da pratica.",
                                                             "turno": i+1, "status": "aprovado" if ok else "reprovado"})
                if any(c["status"] == "reprovado" for c in registro["criterios_automaticos"]):
                    registro["status"] = "reprovado"
            if caso["id"] == "02" and registro["status"] == "pendente_revisao":
                from validar_java_gerado import compilar_resposta
                java = compilar_resposta(registro["turnos"][0]["resposta"], pasta / "java_gerado_02")
                registro["validacao_java"] = java
                registro["criterios_automaticos"].append({"criterio": "Compilar o Java gerado sem corrigir sua fonte.",
                                                         "turno": 1, "status": java["status"]})
                if java["status"] in {"reprovado", "bloqueado"}:
                    registro["status"] = java["status"]
            registro["origem_respostas"] = "Execucao real do fluxo; nenhuma resposta do modelo foi substituida."
            salvar_json(caminho, registro)
            return codigo_saida([registro])
    except Exception as exc:
        registro = json.loads(caminho.read_text()) if caminho.exists() else {"id": caso["id"], "turnos": []}
        registro.update(status="reprovado" if registro["turnos"] else "bloqueado",
                        motivo=str(exc), traceback=traceback.format_exc())
        salvar_json(caminho, registro)
        return codigo_saida([registro])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modo", choices=["local", "pedagogico", "cli", "completo"], default="completo")
    parser.add_argument("--casos", help="IDs separados por virgula; ex.: E3,E4,E6")
    parser.add_argument("--base", type=Path, default=RAIZ / "evidencias" / "execucoes")
    parser.add_argument("--timeout-turno", type=int, default=360)
    parser.add_argument("--worker", help=argparse.SUPPRESS)
    parser.add_argument("--unitarios-worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--diretorio", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.unitarios_worker:
        if args.diretorio is None:
            parser.error("Falta --diretorio")
        resultado = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(RAIZ)))
        salvar_json(args.diretorio / "unitarios_resultado.json", {
            "executados": resultado.testsRun,
            "falhas": [(str(t), detalhe) for t, detalhe in resultado.failures],
            "erros": [(str(t), detalhe) for t, detalhe in resultado.errors],
            "ignorados": [(str(t), motivo) for t, motivo in resultado.skipped],
            "aprovados": resultado.testsRun - len(resultado.failures) - len(resultado.errors) - len(resultado.skipped),
        })
        return 1 if not resultado.wasSuccessful() else 2 if resultado.skipped else 0
    casos = casos_pedagogicos()
    if args.worker:
        return executar_worker(next(c for c in casos if c["id"] == args.worker), args.diretorio)
    if args.timeout_turno <= 0:
        parser.error("--timeout-turno deve ser positivo")
    if args.casos:
        ids = set(args.casos.split(","))
        if ids - {c["id"] for c in casos}:
            parser.error("ID de cenario desconhecido")
        casos = [c for c in casos if c["id"] in ids]
    pasta = nova_execucao(args.base.resolve())
    env = os.environ.copy()
    env.update(OTEL_SDK_DISABLED="true", CREWAI_TELEMETRY_DISABLED="true", CREWAI_TRACING_ENABLED="false",
               XDG_DATA_HOME=str(pasta / "runtime"), PYTHONDONTWRITEBYTECODE="1")
    metadados = manifesto()
    metadados.update(modo=args.modo, casos=[c["id"] for c in casos],
                     ambiente_de_teste={k: env[k] for k in ("OTEL_SDK_DISABLED", "CREWAI_TELEMETRY_DISABLED",
                                                           "CREWAI_TRACING_ENABLED", "XDG_DATA_HOME")})
    salvar_json(pasta / "manifesto.json", metadados)
    registrar_comando([sys.executable, "-m", "pip", "freeze"], pasta, "dependencias", env=env)
    registros = []
    if args.modo in {"local", "completo"}:
        print("Executando testes locais com criterios automaticos...", flush=True)
        unitarios = registrar_comando([sys.executable, "-B", str(Path(__file__).resolve()),
                                      "--unitarios-worker", "--diretorio", str(pasta)], pasta, "unitarios", env=env)
        if unitarios["codigo_saida"] == 2:
            unitarios.update(status="bloqueado", motivo="Existem testes ignorados; consultar unitarios_resultado.json.")
            salvar_json(pasta / "unitarios.json", unitarios)
        registros.append(unitarios)
        if find_spec("crewai"):
            registros.append(registrar_comando([sys.executable, "-B", "test_roteamento.py"], pasta, "roteamento", env=env))
        else:
            registros.append({"id": "roteamento", "status": "bloqueado", "motivo": "CrewAI nao instalado no Python selecionado."})
    if args.modo in {"cli", "completo"}:
        registros.append(registrar_comando([sys.executable, "-B", "test_cli.py", "--saida", str(pasta / "cli")],
                                          pasta, "cli", timeout=args.timeout_turno * 3, env=env))
    if args.modo in {"pedagogico", "completo"}:
        for caso in casos:
            nome = "cenario_" + caso["id"]
            print(f"Executando {nome}: {caso['categoria']}...", flush=True)
            processo = registrar_comando([sys.executable, "-B", str(Path(__file__).resolve()), "--worker", caso["id"],
                                           "--diretorio", str(pasta)], pasta, nome + "_processo",
                                          timeout=args.timeout_turno * len(caso["perguntas"]), env=env)
            caminho = pasta / f"{nome}.json"
            if caminho.exists():
                registro = json.loads(caminho.read_text())
                if registro["status"] == "em_execucao":
                    registro.update(status="reprovado", motivo="Execucao interrompida; turnos concluidos preservados.")
                    salvar_json(caminho, registro)
            else:
                registro = {"id": caso["id"], "status": "bloqueado", "motivo": "Worker nao produziu registro; consulte stdout/stderr."}
                salvar_json(caminho, registro)
            registros.append({"id": caso["id"], "status": registro["status"], "evidencia": caminho.name,
                              "processo": processo["id"] + ".json"})
            escrever_resumo(pasta, registros)
    resumo = escrever_resumo(pasta, registros)
    print(f"Evidencias: {pasta}\nStatus: {resumo['contagens']}", flush=True)
    return resumo["codigo_saida"]


if __name__ == "__main__":
    raise SystemExit(main())
