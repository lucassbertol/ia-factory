"""Chat web local: python -m agente.web (a CLI continua em python -m agente)."""

from __future__ import annotations

import argparse
import json
import logging
import re
from threading import Lock

from starlette.applications import Starlette
from starlette.concurrency import run_in_threadpool
from starlette.middleware import Middleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from .config import OLLAMA_MODEL, PADRAO_ENSINADO, ROOT_DIR
from .erro import (
    ErroEntradaVazia, ErroForaDeEscopo, ErroInventicao,
    ErroModeloIndisponivel, ErroSaidaInesperada, ErroSolucaoPronta,
)
from .memoria import MemoriaConversa

logger = logging.getLogger(__name__)
# Uma chamada por vez evita concorrencia na crew/modelo local e na memoria.
_ocupado = Lock()


def erro(mensagem: str, status: int) -> JSONResponse:
    return JSONResponse({"erro": mensagem}, status_code=status)


def sessao_valida(sessao) -> bool:
    return isinstance(sessao, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", sessao) is not None


def origem_valida(request) -> bool:
    origem = request.headers.get("origin")
    return origem is None or origem == str(request.base_url).rstrip("/")


def responder(pergunta: str, sessao: str) -> JSONResponse:
    if not _ocupado.acquire(blocking=False):
        return erro("A IA está respondendo outra mensagem. Tente novamente em instantes.", 429)
    try:
        # Importacao adiada permite abrir a interface e ver o historico mesmo
        # quando alguma dependencia do sistema multiagente estiver ausente.
        from .fluxo import executar_fluxo

        try:
            resultado = executar_fluxo(pergunta, sessao_id=sessao)
            resposta, tipo = resultado.resposta, "resposta"
        except (ErroInventicao, ErroSolucaoPronta, ErroForaDeEscopo) as exc:
            resposta, tipo = exc.mensagem_usuario, "orientacao"
            # Preserva tambem as orientacoes exibidas para que o reload do chat
            # corresponda ao que o estudante viu, sem alterar a CLI.
            MemoriaConversa(sessao).salvar_turno(pergunta, resposta, "guardiao", intencao="orientacao")
        return JSONResponse({"resposta": resposta, "tipo": tipo, "sessao_id": sessao})
    except ErroEntradaVazia as exc:
        return erro(exc.mensagem_usuario, 400)
    except ErroModeloIndisponivel:
        return erro("Não foi possível acessar o modelo local. Verifique se o Ollama está ativo e tente novamente.", 503)
    except ErroSaidaInesperada:
        return erro("Não foi possível obter uma resposta confiável. Verifique o Ollama ou reformule a pergunta e tente novamente.", 502)
    except ModuleNotFoundError:
        logger.exception("Dependencia ausente na interface web")
        return erro("Faltam dependências do sistema. Instale requirements.txt no ambiente Python do servidor.", 503)
    except Exception:
        logger.exception("Falha ao responder no chat web")
        return erro("Não foi possível concluir a mensagem. Tente novamente.", 500)
    finally:
        _ocupado.release()


async def chat(request):
    if not origem_valida(request):
        return erro("Origem da requisição não permitida.", 403)
    if request.headers.get("content-type", "").split(";")[0].strip() != "application/json":
        return erro("Envie a mensagem no formato JSON.", 415)
    try:
        dados = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError):
        return erro("Mensagem JSON inválida.", 400)
    if not isinstance(dados, dict):
        return erro("Mensagem JSON inválida.", 400)
    pergunta, sessao = dados.get("pergunta"), dados.get("sessao_id")
    if not sessao_valida(sessao):
        return erro("Identificador de conversa inválido.", 400)
    if not isinstance(pergunta, str) or not pergunta.strip():
        return erro("Digite uma pergunta para enviar.", 400)
    if len(pergunta) > 12000:
        return erro("A mensagem deve ter até 12.000 caracteres.", 400)
    return await run_in_threadpool(responder, pergunta.strip(), sessao)


async def info(request):
    return JSONResponse({"padrao": PADRAO_ENSINADO, "modelo": OLLAMA_MODEL})


async def historico(request):
    sessao = request.path_params["sessao"]
    if not sessao_valida(sessao):
        return erro("Identificador de conversa inválido.", 400)
    try:
        turnos = await run_in_threadpool(lambda: MemoriaConversa(sessao).historico)
        return JSONResponse({"sessao_id": sessao, "turnos": turnos})
    except OSError:
        logger.exception("Falha ao ler historico web")
        return erro("Não foi possível carregar o histórico da conversa.", 500)


def limpar_sessao(sessao):
    if not _ocupado.acquire(blocking=False):
        return erro("Aguarde a resposta da IA antes de limpar a conversa.", 429)
    try:
        MemoriaConversa(sessao).limpar()
        return JSONResponse({"sessao_id": sessao, "limpa": True})
    except OSError:
        logger.exception("Falha ao limpar sessao web")
        return erro("Não foi possível limpar a conversa. Tente novamente.", 500)
    finally:
        _ocupado.release()


async def limpar(request):
    if not origem_valida(request):
        return erro("Origem da requisição não permitida.", 403)
    sessao = request.path_params["sessao"]
    if not sessao_valida(sessao):
        return erro("Identificador de conversa inválido.", 400)
    return await run_in_threadpool(limpar_sessao, sessao)


app = Starlette(
    routes=[
        Route("/api/info", info, methods=["GET"]),
        Route("/api/chat", chat, methods=["POST"]),
        Route("/api/sessoes/{sessao}", historico, methods=["GET"]),
        Route("/api/sessoes/{sessao}", limpar, methods=["DELETE"]),
        Mount("/", StaticFiles(directory=ROOT_DIR / "frontend", html=True), name="frontend"),
    ],
    middleware=[Middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])],
    max_body_size=64 * 1024,
)


def main():
    import uvicorn

    parser = argparse.ArgumentParser(description="Interface web local do sistema Factory Method")
    parser.add_argument("--port", type=int, default=8000, help="Porta HTTP local (padrão: 8000)")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("A porta deve estar entre 1 e 65535.")
    uvicorn.run(app, host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
