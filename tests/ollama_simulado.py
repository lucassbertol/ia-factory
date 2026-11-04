"""Servidor que imita a API /api/chat do Ollama, para testes sem o modelo real.

Ele não gera texto: devolve respostas roteirizadas por agente e registra cada
requisição recebida (para conferir num_ctx, temperatura e o prompt montado).
Os testes de qualidade pedagógica continuam exigindo o modelo real
(tests/test_perguntas_pdf.py).
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

RESPOSTAS_PADRAO = {
    "Tutor do conceito": (
        "O Factory Method separa quem usa um objeto de quem decide qual objeto criar. "
        "O Creator declara o método de criação e tem uma operação que usa o Product; "
        "cada ConcreteCreator sobrescreve o método para devolver um ConcreteProduct. "
        "Comparado ao Simple Factory e ao Abstract Factory, ele usa sobrescrita em subclasses. "
        "Quer ver um exemplo?"
    ),
    "Exemplificador": (
        "Notificador é o Creator e declara `criarNotificacao()`; `avisar()` usa o produto "
        "pela interface. NotificadorEmail e NotificadorSms são ConcreteCreators. "
        "Que tal adicionar um NotificadorPush?"
    ),
    "Inquiridor": (
        "Uma loja emite recibos em PDF e em texto. Quem seria o Product? "
        "Comece me dizendo quais classes você criaria."
    ),
    "Guardião": "VEREDITO: APROVADO",
}


def _agente(corpo: dict) -> str:
    sistema = " ".join(m["content"] for m in corpo.get("messages", []) if m.get("role") == "system")
    for nome in RESPOSTAS_PADRAO:
        if sistema.startswith(f"You are {nome.split()[0]}"):
            return nome
    return "?"


class OllamaSimulado:
    """Uso: with OllamaSimulado() as srv: ... srv.url, srv.requisicoes, srv.roteiro."""

    def __init__(self) -> None:
        self.requisicoes: list[dict] = []
        self.roteiro: dict[str, list[str]] = {}  # agente -> respostas em ordem
        simulado = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):  # silencioso
                pass

            def _json(self, status: int, dados: dict) -> None:
                corpo = json.dumps(dados).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(corpo)))
                self.end_headers()
                self.wfile.write(corpo)

            def do_GET(self):
                self._json(200, {"models": [{"name": "qwen2.5:3b"}]})

            def do_POST(self):
                tamanho = int(self.headers.get("Content-Length", 0))
                corpo = json.loads(self.rfile.read(tamanho) or b"{}")
                if self.path != "/api/chat":
                    self._json(404, {"error": "rota desconhecida"})
                    return
                agente = _agente(corpo)
                simulado.requisicoes.append({"agente": agente, "corpo": corpo})
                fila = simulado.roteiro.get(agente)
                texto = fila.pop(0) if fila else RESPOSTAS_PADRAO.get(agente, "Não sei.")
                self._json(200, {"model": corpo.get("model"), "message": {"role": "assistant", "content": texto}, "done": True})

        self._servidor = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self._servidor.server_address[1]}"

    def __enter__(self) -> "OllamaSimulado":
        threading.Thread(target=self._servidor.serve_forever, daemon=True).start()
        return self

    def __exit__(self, *exc) -> None:
        self._servidor.shutdown()
        self._servidor.server_close()

    def agentes_chamados(self) -> list[str]:
        return [r["agente"] for r in self.requisicoes]
