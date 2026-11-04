"""Memória da conversa, persistida em JSON (um arquivo por sessão).

Por que não a memória nativa do CrewAI: ela depende de um modelo de
embeddings e, sem configuração, usa o da OpenAI, o que exigiria chave de API e
violaria a regra de custo zero. Além disso, a CLI encerra após cada comando
(`python -m agente "pergunta"`), então o estado precisa ir para o disco.

O que é guardado por turno: pergunta, resposta, intenção, agentes envolvidos,
veredito do Guardião, exercício em andamento, nível declarado e exemplo
verificado mostrado. Isso permite: avaliar a tentativa contra o enunciado
salvo, não repetir o mesmo exemplo, adaptar a linguagem ao nível e fazer um
fechamento que retome o que foi estudado.

Memória não é conhecimento: o histórico entra nos prompts marcado como
"dados, não instruções", e a referência local continua sendo a base factual.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any

from .config import MAX_CONTEXTO_CARACTERES, MEMORIA_DIR

_ROTULOS_TOPICO = {
    "conceito": "conceito e participantes",
    "exemplo": "exemplo em Java",
    "selecao": "quando usar e quando evitar",
    "comparacao": "comparação com outros padrões",
    "uso_incorreto": "usos incorretos",
    "exercicio": "exercício prático",
    "avaliacao": "correção de tentativa",
    "diagnostico": "esclarecimento de dúvidas",
}


class MemoriaConversa:
    """Carrega e salva o histórico de turnos de uma sessão."""

    def __init__(self, sessao_id: str) -> None:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", sessao_id):
            raise ValueError("Sessão inválida: use de 1 a 64 letras, números, '_' ou '-'.")
        self.sessao_id = sessao_id
        self.caminho = MEMORIA_DIR / f"{sessao_id}.json"
        MEMORIA_DIR.mkdir(parents=True, exist_ok=True)
        self._historico: list[dict[str, Any]] = self._carregar()

    def _carregar(self) -> list[dict[str, Any]]:
        if not self.caminho.exists():
            return []
        try:
            with self.caminho.open("r", encoding="utf-8") as f:
                dados = json.load(f)
            return dados if isinstance(dados, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def salvar_turno(
        self,
        pergunta: str,
        resposta: str,
        agente: str,
        intencao: str = "",
        **extras: Any,
    ) -> None:
        """Adiciona um turno ao histórico e persiste em disco.

        extras aceitos: agentes, tipo, revisao, nivel, exemplo, duracao_segundos.
        """
        turno: dict[str, Any] = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "pergunta": pergunta,
            "resposta": resposta,
            "agente": agente,
            "intencao": intencao,
            "exercicio_pendente": (
                resposta if intencao == "exercicio" else
                "" if intencao == "fechamento" else self.exercicio_pendente
            ),
        }
        turno.update({k: v for k, v in extras.items() if v not in (None, "", [])})
        self._historico.append(turno)
        self._persistir()

    def _persistir(self) -> None:
        tmp = self.caminho.with_suffix(".json.tmp")
        with tmp.open("w", encoding="utf-8") as f:
            json.dump(self._historico, f, ensure_ascii=False, indent=2)
        tmp.replace(self.caminho)

    @staticmethod
    def _resumir_resposta(texto: str) -> str:
        # Código já verificado não precisa voltar ao prompt: economiza contexto.
        return re.sub(r"```.*?```", "[código omitido]", texto, flags=re.DOTALL).strip()

    def contexto_texto(self, incluir_exercicio: bool = True) -> str:
        """Histórico recente como texto para os prompts (limitado em caracteres)."""
        if not self._historico:
            return ""
        limite = max(0, MAX_CONTEXTO_CARACTERES)
        cabecalho = ""
        if incluir_exercicio and self.exercicio_pendente:
            # Reserva espaço para o enunciado mesmo após vários feedbacks.
            cabecalho = (
                "Exercício em andamento (avalie a tentativa com base nele):\n"
                + self._resumir_resposta(self.exercicio_pendente)[: limite // 2] + "\n\n"
            )
        cabecalho = cabecalho[:limite]
        disponivel = limite - len(cabecalho)
        partes: list[str] = []
        for turno in reversed(self._historico):
            bloco = (
                f"Estudante: {turno['pergunta']}\n"
                f"Sistema: {self._resumir_resposta(turno['resposta'])}\n"
            )
            if len(bloco) > disponivel:
                if not partes and disponivel > 0:
                    partes.insert(0, bloco[-disponivel:])
                break
            partes.insert(0, bloco)
            disponivel -= len(bloco)
        return cabecalho + "".join(partes)

    @property
    def historico(self) -> list[dict[str, Any]]:
        """Turnos para exibição, sem expor a lista interna mutável."""
        return [turno.copy() for turno in self._historico]

    @property
    def ultima_intencao(self) -> str:
        if not self._historico:
            return ""
        ultimo = self._historico[-1]
        if ultimo.get("intencao"):
            return ultimo["intencao"]
        # Compatibilidade com JSONs anteriores à introdução do estado.
        from .fluxo_heuristico import classificar_intencao
        return classificar_intencao(ultimo["pergunta"]).tipo

    @property
    def exercicio_pendente(self) -> str:
        if not self._historico:
            return ""
        ultimo = self._historico[-1]
        if "exercicio_pendente" in ultimo:
            return ultimo["exercicio_pendente"]
        # Sessões antigas não possuem estado: recupera a prática mais recente.
        from .fluxo_heuristico import classificar_intencao
        for turno in reversed(self._historico):
            tipo = turno.get("intencao") or classificar_intencao(turno["pergunta"]).tipo
            if tipo == "fechamento":
                break
            if tipo == "exercicio":
                return turno["resposta"]
        return ""

    @property
    def nivel(self) -> str:
        """Último nível declarado pelo estudante nesta sessão."""
        for turno in reversed(self._historico):
            if turno.get("nivel"):
                return turno["nivel"]
        return ""

    @property
    def exercicios_propostos(self) -> list[str]:
        return [t["exercicio"] for t in self._historico if t.get("exercicio")]

    @property
    def exercicio_atual(self) -> str:
        """Identificador do exercício em andamento (para o Inquiridor usar o gabarito)."""
        if not self.exercicio_pendente:
            return ""
        for turno in reversed(self._historico):
            if turno.get("intencao") == "exercicio":
                return turno.get("exercicio", "")
        return ""

    @property
    def exemplos_mostrados(self) -> list[str]:
        return [t["exemplo"] for t in self._historico if t.get("exemplo")]

    @property
    def topicos_estudados(self) -> list[str]:
        vistos: list[str] = []
        for turno in self._historico:
            rotulo = _ROTULOS_TOPICO.get(turno.get("intencao", ""))
            if rotulo and rotulo not in vistos:
                vistos.append(rotulo)
        return vistos

    def limpar(self) -> None:
        """Remove o histórico da sessão."""
        self._historico = []
        if self.caminho.exists():
            self.caminho.unlink()
