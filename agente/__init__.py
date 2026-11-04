"""Sistema multiagente pedagógico para o padrão Factory Method.

Projeto final da disciplina ELC1070 - Análise e Projeto de Sistemas OO (UFSM).
Tecnologias: Python + CrewAI + Ollama (qwen2.5:3b), custo zero.
Interface: CLI via `python -m agente "pergunta aqui"`.
"""

import os

# Execução 100% local: desliga telemetria e rastreamento do CrewAI antes de
# qualquer import do framework. Sem isso, o CrewAI tenta enviar dados de uso
# pela internet e, na primeira execução, pergunta no terminal se o usuário
# quer ver "traces" (o que travaria a CLI por alguns segundos na demonstração).
for _variavel, _valor in {
    "OTEL_SDK_DISABLED": "true",
    "CREWAI_DISABLE_TELEMETRY": "true",
    "CREWAI_DISABLE_TRACKING": "true",
    "CREWAI_TRACING_ENABLED": "false",
}.items():
    os.environ.setdefault(_variavel, _valor)

# Falhas do modelo já são explicadas ao estudante por agente/erro.py; os logs
# internos do framework repetiriam a mesma falha em inglês no terminal.
# Use AGENTE_DEBUG=1 para vê-los.
if not os.getenv("AGENTE_DEBUG"):
    import logging

    logging.getLogger("crewai.flow.runtime").setLevel(logging.CRITICAL)

__version__ = "0.2.0"
