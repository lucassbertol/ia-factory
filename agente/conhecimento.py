"""Leitura e seleção do material didático em referencias/factory_method.md.

O Markdown é a fonte única; códigos e gabaritos não entram na referência
conceitual compartilhada. O material é carregado ao iniciar o processo.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

from .config import REFERENCIAS_DIR


def _ler_secoes(texto: str) -> dict[str, str]:
    """Lê títulos `## [identificador] Título`, ignorando títulos em cercas."""
    secoes: dict[str, str] = {}
    atual = None
    linhas: list[str] = []
    cerca = ""

    def salvar():
        if atual is not None:
            conteudo = "\n".join(linhas).strip()
            if not conteudo:
                raise ValueError(f"Seção vazia na referência: {atual}")
            secoes[atual] = conteudo

    for linha in texto.splitlines():
        delimitador = re.match(r"^\s*(`{3,}|~{3,})(.*)$", linha)
        if delimitador:
            marca, resto = delimitador.groups()
            if not cerca:
                cerca = marca
            elif marca[0] == cerca[0] and len(marca) >= len(cerca) and not resto.strip():
                cerca = ""
            linhas.append(linha)
            continue
        titulo = re.fullmatch(r"## \[([a-z0-9_:-]+)\] .+", linha) if not cerca else None
        if titulo:
            salvar()
            atual = titulo.group(1)
            if atual in secoes:
                raise ValueError(f"Seção duplicada na referência: {atual}")
            linhas = []
        elif atual is not None:
            linhas.append(linha)
    if cerca:
        raise ValueError("Cerca de código não encerrada na referência")
    salvar()
    if not secoes:
        raise ValueError("Referência sem seções identificadas")
    return secoes


def _obter(secoes: dict[str, str], ident: str) -> str:
    if ident not in secoes:
        raise ValueError(f"Seção obrigatória ausente na referência: {ident}")
    return secoes[ident]


def _bloco(secoes: dict[str, str], ident: str, linguagem: str) -> str:
    texto = _obter(secoes, ident)
    achado = re.fullmatch(r"```" + linguagem + r"\n(.*?)\n```", texto, re.DOTALL)
    if not achado or not achado.group(1).strip():
        raise ValueError(f"Bloco {linguagem} inválido na referência: {ident}")
    return achado.group(1)


_SECOES = _ler_secoes((REFERENCIAS_DIR / "factory_method.md").read_text(encoding="utf-8"))
_BASE = ("definicao", "problema", "participantes", "cuidados", "confiabilidade", "fontes")
_POR_INTENCAO = {
    "conceito": ("consequencias", "selecao"),
    "selecao": ("consequencias", "selecao"),
    "comparacao": ("comparacao",),
    "exemplo": ("distincoes",),
    "uso_incorreto": ("usos_incorretos", "distincoes"),
    "diagnostico": ("comparacao", "usos_incorretos", "distincoes"),
    "avaliacao": ("comparacao", "usos_incorretos"),
    "esclarecimento": ("comparacao", "usos_incorretos"),
    "fechamento": ("consequencias", "selecao", "comparacao", "usos_incorretos"),
    "exercicio": ("comparacao", "usos_incorretos"),
}
for _ident in dict.fromkeys(_BASE + tuple(i for ids in _POR_INTENCAO.values() for i in ids)):
    _obter(_SECOES, _ident)


def carregar_referencia(intencao: str = "conceito") -> str:
    """Seleciona conceitos; nunca inclui exercícios, gabaritos ou código Java."""
    ids = _BASE + _POR_INTENCAO.get(intencao, _POR_INTENCAO["conceito"])
    return "\n\n".join(f"## [{ident}]\n{_obter(_SECOES, ident)}" for ident in ids)


def carregar_uml() -> str:
    return _bloco(_SECOES, "uml", "text")


@dataclass(frozen=True)
class ExemploJava:
    arquivo: str
    titulo: str
    saida_esperada: str
    codigo: str

    def bloco_markdown(self) -> str:
        return (
            f"**{self.titulo}** (arquivo `{self.arquivo}`, compilado e executado pela dupla)\n\n"
            f"```java\n{self.codigo}\n```\n\n"
            f"Saída ao executar `java {self.arquivo[:-5]}`:\n\n```\n{self.saida_esperada}\n```"
        )


EXEMPLOS: dict[str, ExemploJava] = {}
FATOS_EXEMPLOS: dict[str, str] = {}
for _secao in _SECOES:
    if _secao.startswith("exemplo:") and _secao.endswith(":arquivo"):
        _id = _secao.split(":")[1]
        _prefixo = f"exemplo:{_id}:"
        EXEMPLOS[_id] = ExemploJava(
            arquivo=_obter(_SECOES, _prefixo + "arquivo"),
            titulo=_obter(_SECOES, _prefixo + "titulo"),
            saida_esperada=_bloco(_SECOES, _prefixo + "saida", "text"),
            codigo=_bloco(_SECOES, _prefixo + "codigo", "java"),
        )
        if _id != "simple_factory":
            FATOS_EXEMPLOS[_id] = _obter(_SECOES, _prefixo + "fatos")
for _id in ("basico", "padrao", "incorreto", "simple_factory"):
    if _id not in EXEMPLOS:
        raise ValueError(f"Exemplo obrigatório ausente na referência: {_id}")

CORRECAO_USO_INCORRETO = _obter(_SECOES, "correcao_uso_incorreto")


@dataclass(frozen=True)
class Exercicio:
    ident: str
    enunciado: str
    gabarito: str


EXERCICIOS = [
    Exercicio(
        ident=secao.split(":")[1],
        enunciado=_obter(_SECOES, secao),
        gabarito=_obter(_SECOES, secao.removesuffix("enunciado") + "gabarito"),
    )
    for secao in _SECOES
    if secao.startswith("exercicio:") and secao.endswith(":enunciado")
]
if not EXERCICIOS:
    raise ValueError("Banco de exercícios vazio na referência")
carregar_uml()


def escolher_exemplo(nivel: str, ja_mostrados: list[str]) -> str:
    """Escolhe qual exemplo verificado mostrar.

    Iniciantes começam pelo exemplo básico; nível intermediário/avançado começa
    pela variação com Creator concreto (ensina que o Creator não precisa ser
    abstrato). Um novo pedido de exemplo na mesma sessão recebe o que ainda não
    foi visto, usando a memória da conversa.
    """
    ordem = ["padrao", "basico"] if nivel in {"intermediario", "avancado"} else ["basico", "padrao"]
    vistos = [e for e in ja_mostrados if e in ordem]
    if not vistos:
        return ordem[0]
    for exemplo in ordem:  # um pedido repetido recebe o exemplo ainda não visto
        if exemplo not in vistos:
            return exemplo
    # Ambos já vistos: alterna em relação ao último mostrado.
    return "padrao" if vistos[-1] == "basico" else "basico"


def escolher_exercicio(ja_propostos: list[str]) -> Exercicio:
    """Próximo exercício ainda não proposto na sessão (volta ao início depois)."""
    for exercicio in EXERCICIOS:
        if exercicio.ident not in ja_propostos:
            return exercicio
    ultimo = ja_propostos[-1] if ja_propostos else ""
    return next((e for e in EXERCICIOS if e.ident != ultimo), EXERCICIOS[0])


def exercicio_por_id(ident: str) -> Exercicio | None:
    return next((e for e in EXERCICIOS if e.ident == ident), None)
