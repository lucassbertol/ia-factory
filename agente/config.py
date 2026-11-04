"""Configurações centralizadas do sistema multiagente pedagógico.

Valores podem ser sobrescritos por variáveis de ambiente, sem editar o código.
"""

import os
from pathlib import Path

# Diretórios
ROOT_DIR = Path(__file__).resolve().parent.parent
AGENTE_DIR = Path(__file__).resolve().parent
REFERENCIAS_DIR = AGENTE_DIR / "referencias"
MEMORIA_DIR = Path(os.getenv("AGENTE_MEMORIA_DIR", str(ROOT_DIR / "memoria" / "sessoes")))

# Servidor Ollama local (custo zero). Só endereços locais são usados.
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

# Parâmetros de geração enviados ao Ollama em toda chamada.
# num_ctx: a janela padrão do Ollama é pequena e corta o início do prompt
# (justamente as regras do agente). 8192 tokens cabem com folga em 16 GB.
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "8192"))
# Temperatura baixa: menos variação e menos invenção em respostas conceituais.
OLLAMA_TEMPERATURA = float(os.getenv("OLLAMA_TEMPERATURA", "0.2"))
# Limite de tokens gerados por chamada: mantém respostas curtas e rápidas.
OLLAMA_NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "800"))
# Penalidade de repetição (1.0 = nenhuma). Evita laços de frases repetidas.
OLLAMA_REPEAT_PENALTY = float(os.getenv("OLLAMA_REPEAT_PENALTY", "1.15"))
# Tempo limite (segundos) de cada chamada ao modelo local.
OLLAMA_TIMEOUT_SEGUNDOS = int(os.getenv("OLLAMA_TIMEOUT_SEGUNDOS", "180"))

# Histórico injetado nos prompts (caracteres).
MAX_CONTEXTO_CARACTERES = int(os.getenv("MAX_CONTEXTO_CARACTERES", "2000"))

# Uma rodada de correção, sempre seguida de nova revisão. Zero desliga apenas
# a correção: respostas sem aprovação continuam bloqueadas. Nunca excede 1.
MAX_REESCRITAS_GUARDIAO = max(0, min(1, int(os.getenv("MAX_REESCRITAS_GUARDIAO", "1"))))

# Tamanho máximo aceito para o texto de um agente antes de pedir resumo.
MAX_CARACTERES_RESPOSTA = int(os.getenv("MAX_CARACTERES_RESPOSTA", "2600"))

PADRAO_ENSINADO = "Factory Method"

NIVEIS = ("iniciante", "intermediario", "avancado")
