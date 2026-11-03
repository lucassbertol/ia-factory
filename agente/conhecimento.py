"""Referencia conceitual e exemplos locais, sem acesso a rede."""

from pathlib import Path

REFERENCIAS_DIR = Path(__file__).resolve().parent / "referencias"


def carregar_referencia() -> str:
    """Le a sintese que fundamenta as instrucoes de todos os agentes."""
    conteudo = (REFERENCIAS_DIR / "factory_method.md").read_text(encoding="utf-8")
    if not conteudo.strip():
        raise ValueError("Referencia conceitual local vazia: factory_method.md")
    return conteudo


def carregar_exemplos_java() -> str:
    """Fornece os arquivos integrais e identifica seu papel pedagogico."""
    blocos = []
    for nome in ("ExemploFactoryMethod.java", "ExemploSimpleFactory.java"):
        codigo = (REFERENCIAS_DIR / nome).read_text(encoding="utf-8")
        blocos.append(f"Arquivo de referencia: {nome}\n```java\n{codigo}```")
    return "\n\n".join(blocos)
