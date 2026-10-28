"""Configuracoes centralizadas do sistema multiagente pedagógico.

Todas as configuracoes de ambiente ficam aqui para facilitar a manutencao
e a reproducao da execucao em uma instalacao limpa.
"""

import os
from pathlib import Path

# Diretorio raiz do projeto
ROOT_DIR = Path(__file__).resolve().parent.parent

# Diretorio do pacote
AGENTE_DIR = Path(__file__).resolve().parent

# Diretorio de prompts do sistema
PROMPTS_DIR = AGENTE_DIR / "prompts"

# Diretorio de sessoes da memoria (criado em tempo de execucao)
MEMORIA_DIR = ROOT_DIR / "memoria" / "sessoes"

# Servidor Ollama local
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

# Modelo local (custo zero, 8 GB de RAM)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

# Limite de caracteres do historico injetado no contexto (evita respostas longas demais)
MAX_CONTEXTO_CARACTERES = int(os.getenv("MAX_CONTEXTO_CARACTERES", "2000"))

# Tempo limite (segundos) para chamadas ao modelo local
OLLAMA_TIMEOUT_SEGUNDOS = int(os.getenv("OLLAMA_TIMEOUT_SEGUNDOS", "120"))

# Padrao ensinado pelo sistema
PADRAO_ENSINADO = "Factory Method"

# Linguagem dos exemplos de codigo (conforme o roteiro de avaliacao)
LINGUAGEM_EXEMPLOS = "Java"

# Comando obrigatorio da CLI
CLI_COMANDO = 'python -m agente "pergunta aqui"'

# Custo zero: sem API paga
API_PAGA_PERMITIDA = False
