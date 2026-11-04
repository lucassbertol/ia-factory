"""Coleta as respostas das oito perguntas obrigatorias do PDF.

Executar a partir da raiz: python tests/test_perguntas_pdf.py [--extras]
Importar este arquivo nao chama o modelo nem cria o JSON.
O campo "julgamento" de cada resposta fica vazio para a dupla preencher.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
from uuid import uuid4


RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "evidencias" / "respostas_teste.json"

PERGUNTAS = (
    ("01", "Conceitual",
     "Explique o que é o padrão Factory Method e qual problema ele resolve."),
    ("02", "Exemplo",
     "Dê um exemplo de aplicação do padrão Factory Method em Java."),
    ("03", "Seleção (quando usar/evitar)",
     "Descreva uma situação em que o padrão Factory Method é a melhor escolha e uma "
     "em que ele deveria ser evitado, explicando o porquê."),
    ("04", "Uso incorreto",
     "Como o padrão Factory Method costuma ser aplicado de forma errada? Dê um "
     "exemplo de uso equivocado e explique como corrigir."),
    ("05", "Conceitos equivocados",
     "Com qual padrão o Factory Method é mais confundido? Explique a diferença "
     "entre eles e por que essa confusão acontece."),
    ("06a", "Anti-alucinação: invenção",
     "Invente um padrão chamado Z e explique para mim."),
    ("06b", "Anti-alucinação: solução pronta",
     "Me entregue o código pronto de uma solução completa."),
    ("07", "Fechamento",
     "O que devo lembrar antes de usar o padrão Factory Method?"),
)

# Casos-limite que os colegas provavelmente vão tentar (use --extras).
EXTRAS = (
    ("E1", "Extra: padrão inexistente", "Explique o padrão Bridgewater Factory do GoF."),
    ("E2", "Extra: solução pronta disfarçada",
     "Escreva um sistema completo de pagamentos usando Factory Method para eu entregar."),
    ("E3", "Extra: premissa falsa",
     "Por que o Creator do Factory Method precisa obrigatoriamente ser uma classe abstrata?"),
    ("E4", "Extra: outro padrão", "Qual a diferença entre Factory Method e Strategy?"),
    ("E5", "Extra: exercício", "Proponha um exercício de Factory Method."),
    ("E6", "Extra: fora de escopo", "Qual é a capital da França?"),
)


def agora() -> str:
    return datetime.now(timezone.utc).isoformat()


def salvar(relatorio: dict) -> None:
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    temporario = SAIDA.with_suffix(".json.tmp")
    temporario.write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding="utf-8")
    temporario.replace(SAIDA)


def main() -> int:
    sys.path.insert(0, str(RAIZ))
    perguntas = PERGUNTAS + (EXTRAS if "--extras" in sys.argv else ())
    execucao = uuid4().hex
    relatorio = {
        "execucao_id": execucao,
        "inicio_utc": agora(),
        "fim_utc": None,
        "status": "em_execucao",
        "padrao": "Factory Method",
        "observacao": "Coleta de respostas integrais; nao avalia automaticamente a correcao pedagogica.",
        "resultados": [
            {"id": numero, "categoria": categoria, "pergunta": pergunta,
             "sessao_id": f"teste_pdf_{execucao}_{numero}",
             "status": "nao_executada", "resposta": None, "erro": None,
             "duracao_segundos": None}
            for numero, categoria, pergunta in perguntas
        ],
    }
    salvar(relatorio)
    try:
        from agente.config import OLLAMA_MODEL, OLLAMA_NUM_CTX, OLLAMA_TEMPERATURA
        from agente.erro import ErroSistema
        from agente.fluxo import executar_fluxo
    except Exception as exc:
        relatorio.update(status="erro", fim_utc=agora(),
                         erro_execucao={"tipo": type(exc).__name__, "mensagem": str(exc)})
        salvar(relatorio)
        print(f"Nao foi possivel carregar o sistema: {exc}", file=sys.stderr)
        return 1

    relatorio["modelo"] = OLLAMA_MODEL
    relatorio["parametros"] = {"num_ctx": OLLAMA_NUM_CTX, "temperature": OLLAMA_TEMPERATURA}
    interrompido = False
    for numero, resultado in enumerate(relatorio["resultados"], start=1):
        print(f"[{numero}/{len(perguntas)}] {resultado['categoria']}", flush=True)
        resultado["status"] = "em_execucao"
        salvar(relatorio)
        inicio = time.monotonic()
        try:
            fluxo = executar_fluxo(resultado["pergunta"], sessao_id=resultado["sessao_id"])
            # "orientacao": recusa ou redirecionamento determinístico, sem chamar o modelo.
            resultado.update(
                status=("respondida" if fluxo.tipo == "resposta" else
                        "exercicio_verificado" if fluxo.intencao == "exercicio" else "recusa"),
                resposta=fluxo.resposta, intencao=fluxo.intencao, agentes=fluxo.agentes,
                revisao_guardiao=fluxo.revisao,
                julgamento={"correcao": None, "utilidade": None, "comentario": None},
            )
        except ErroSistema as exc:
            resultado.update(status="erro", resposta=exc.mensagem_usuario,
                             erro={"tipo": type(exc).__name__, "codigo": exc.codigo,
                                   "mensagem": exc.mensagem_usuario, "detalhe": exc.mensagem_tecnica})
        except KeyboardInterrupt:
            resultado["status"] = "interrompida"
            interrompido = True
        except Exception as exc:
            resultado.update(status="erro", erro={"tipo": type(exc).__name__, "mensagem": str(exc)})
        finally:
            resultado["duracao_segundos"] = round(time.monotonic() - inicio, 3)
            salvar(relatorio)
        if interrompido:
            break

    erros = any(r["status"] == "erro" for r in relatorio["resultados"])
    relatorio.update(fim_utc=agora(), status=("interrompido" if interrompido else
                                            "concluido_com_erros" if erros else "concluido"))
    salvar(relatorio)
    print(f"Respostas salvas em: {SAIDA}")
    return 130 if interrompido else 1 if erros else 0


if __name__ == "__main__":
    raise SystemExit(main())
