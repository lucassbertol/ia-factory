"""Verificações determinísticas das respostas (guardrails do CrewAI).

Cada tarefa de um agente autor recebe um ValidadorDeterministico como
`guardrail`. Na primeira tentativa, se houver problema objetivo (código em
outra linguagem, papéis trocados, resposta longa demais...), o CrewAI devolve a
lista de problemas ao próprio agente e pede uma nova versão. Na segunda
tentativa o validador não reprova mais: aplica correções mecânicas (remove
blocos de código, rótulos de meta-revisão) e libera o texto. Assim o tempo de
resposta fica limitado e a CLI nunca quebra por causa de um guardrail.

As regras cobrem erros que de fato apareceram nas evidências de teste com o
qwen2.5:3b (ex.: "ConcreteProduct sobrescreve o factory method", resposta com
código C#, "o Factory Method é confundido com o Factory Method").
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from .config import MAX_CARACTERES_RESPOSTA


def _normaliza(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


_CODIGO_OUTRA_LINGUAGEM = re.compile(
    r"```\s*(?:c#|csharp|cs|python|py|cpp|c\+\+|javascript|js|typescript|ts|php|kotlin|go|ruby)\b"
    r"|\busing System\b|\bConsole\.Write|\bpublic override\b|\)\s*:\s*base\(|\bdef __init__\b"
    r"|#include\s*<|\bconsole\.log\(",
    re.IGNORECASE,
)

# (expressão sobre o texto normalizado, mensagem de correção)
_AFIRMACOES_ERRADAS = [
    (r"concrete\s*products?\b[^.]{0,80}\bsobrescrev",
     "Quem sobrescreve o factory method é o ConcreteCreator, não o ConcreteProduct."),
    (r"\bproducts?\b[^.]{0,40}\b(?:fornece|contem|e) a implementacao concreta",
     "Product é o contrato (interface); a implementação concreta está no ConcreteProduct."),
    (r"simple factory[^.]{0,60}?(?<!nao )\b(?:e|eh)\s+(?:um|uma)\s+(?:dos\s+)?(?:23\s+)?padr(?:ao|oes)\s+(?:do\s+)?(?:catalogo\s+)?(?:gof|gang)",
     "Simple Factory não é um padrão do catálogo GoF; é um idioma útil, sem sobrescrita."),
    (r"(?:creator|criador|factory method|metodo de criacao|metodo fabrica)[^.]{0,50}"
     r"(?<!nao )(?:precisa|precisam|deve|devem|tem que|tem de)\s+"
     r"(?:sempre\s+|obrigatoriamente\s+|necessariamente\s+)?ser\s+(?:uma\s+|um\s+)?(?:classe\s+|metodo\s+)?abstrat",
     "Creator e factory method não precisam ser abstratos: podem ter implementação padrão."),
    (_FM_NAO_GOF := r"factory method[^.]{0,40}?(?<!simple )\bnao\s+(?:e|eh)\s+(?:um\s+)?padr(?:ao|oes)\s+(?:do\s+)?(?:catalogo\s+)?gof"
     r"|nao demonstra o (?:padrao )?(?:factory method )?(?:do )?gof"
     r"|(?:o )?factory method (?:e|eh) (?:um |apenas um |so um )?padrao de sobrescrita",
     "O Factory Method é um padrão criacional do catálogo GoF, e o exemplo mostrado o demonstra."),
    (r"confundid[oa]s?\s+com\s+(?:o\s+)?(?:proprio\s+)?(?:padrao\s+)?factory method\b",
     "O Factory Method não pode ser confundido com ele mesmo: cite Simple Factory ou Abstract Factory."),
    (r"(?:elimina|remove|acaba com)\s+(?:todo|todos os|qualquer|completamente o)\s+(?:uso do\s+)?`?new`?",
     "O `new` não desaparece: ele fica dentro dos ConcreteCreators."),
    (r"\bstrategy\b[^.]{0,80}\bsobrescri\w*",
     "Strategy funciona por composição: o Context recebe uma Strategy e pode trocá-la; não é sobrescrita em subclasses."),
    (r"(?:email|sms)\b[^.]{0,30}\bsao responsave\w* (?:por|pela) (?:implementar )?(?:essa |a )?cria",
     "Email e Sms são ConcreteProducts: quem cria são os ConcreteCreators (NotificadorEmail, NotificadorSms)."),
    (r"https?://", "Não cite links: use apenas a referência local."),
]

_INGLES = re.compile(r"\b(?:the|and|is|are|this|that|with|which|you|of)\b", re.IGNORECASE)


@dataclass
class Exigencias:
    """O que a resposta de um agente precisa conter neste turno."""

    sem_codigo: bool = True
    termos_obrigatorios: list[tuple[str, ...]] = field(default_factory=list)
    descricao_termos: str = ""
    max_caracteres: int = MAX_CARACTERES_RESPOSTA


# Linhas de "bastidor" que o modelo pequeno às vezes escreve (observadas no
# teste real de 04/11): eco da pergunta, rótulos e comentários sobre a revisão.
_LINHAS_META = re.compile(
    r"^\s*(?:[#>*_\s]*)(?:"
    r"(?:thought|pensamento)\s*:.*"
    r"|pergunta do estudante\s*:.*"
    r"|esta e a (?:sua |minha )?pergunta.*"
    r"|(?:essa|esta) e a pergunta guia.*"
    r"|agrade[cç]o (?:a|pela) corre[cç][aã]o.*"
    r"|vou(?:mo)? (?:explicar|reescrever|corrigir) .{0,80}(?:mais precisa|corrigid|revis).*"
    r"|(?:resposta (?:final )?revisada|resposta final|final answer)\s*:?"
    r"|pergunta (?:do inquiridor|para o estudante|guia)\s*:?\**\s*"
    r"|aqui esta (?:uma|a) (?:resposta|explicacao)\b.*"
    r"|(?:esta|essa) pergunta (?:convida|ajuda|serve|incentiva|estimula)\b.*"
    r"|.*\b(?:faria|perguntaria|faca|pergunte) (?:ao|para o) estudante\b.*"
    r"|.*\bbase factual\b.*"
    r"|(?:claro|entendido|certo|ok|perfeito)[!.,]?\s+(?:vou|vamos|voua|irei)\w*\b.*"

    r"|\**\s*\d*\.?\s*\**confiabilidade\**\s*:.*"
    r")\s*$",
    re.IGNORECASE,
)


def remover_meta_revisao(texto: str) -> str:
    """Remove ecos da pergunta, rótulos e comentários sobre o processo."""
    # Frases em terceira pessoa ("o estudante deve...") viram segunda pessoa
    # quando são instrução útil; as demais menções ao estudante são bastidor.
    texto = re.sub(r"\b[Oo] estudante deve fazer\b", "você deve fazer", texto)
    texto = re.sub(r"^\s*\**agora,? o estudante\s*:\**\s*", "", texto, flags=re.IGNORECASE | re.MULTILINE)
    texto = "\n".join(_remover_frases_meta(linha) for linha in texto.splitlines())
    linhas = []
    for linha in texto.strip().splitlines():
        if _LINHAS_META.match(_normaliza(linha)):
            continue
        # Rótulo no início da linha seguido de conteúdo útil.
        linha = re.sub(
            r"^\s*\**(?:resposta\s+final\s+revisada|resposta\s+revisada|resposta\s+final|final answer|"
            r"pergunta do inquiridor|pergunta para o estudante)\s*:\**\s*",
            "", linha, flags=re.IGNORECASE,
        )
        linhas.append(linha)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(linhas)).strip()


_FRASE_META = re.compile(
    r"\b(?:o|ao|do|para o) estudante\b"
    r"|desculpe (?:pela|a|qualquer) confusao"
    r"|esta e (?:a )?(?:sua )?(?:primeira )?pergunta guia"
    r"|com base nas suas respostas, faremos"
    r"|(?:que|o que) voce me mostrou"
    r"|\bouvi voce\b"
    r"|\bcomo guia, pergunte\b"
)


def _remover_frases_meta(linha: str) -> str:
    """Remove, dentro de uma linha, frases que falam do estudante em terceira pessoa."""
    if linha.rstrip().endswith(":"):
        return linha
    frases = re.split(r"(?<=[.!?])\s+", linha)
    mantidas = [f for f in frases if not _FRASE_META.search(_normaliza(f))]
    return " ".join(mantidas) if len(mantidas) != len(frases) else linha


def remover_frases_erradas(texto: str) -> str:
    """Remove frases com erro factual conhecido (último recurso do guardrail)."""
    linhas = []
    for linha in texto.splitlines():
        frases = re.split(r"(?<=[.!?])\s+", linha)
        mantidas = [f for f in frases
                    if not any(re.search(e, _normaliza(f)) for e, _ in _AFIRMACOES_ERRADAS)]
        if mantidas or not linha.strip():
            linhas.append(" ".join(mantidas))
    return "\n".join(linhas).strip()


def _chave_frase(frase: str) -> str:
    return re.sub(r"\W+", " ", _normaliza(frase)).strip()


def contar_repeticoes(texto: str) -> int:
    """Quantas frases (com 5+ palavras) aparecem repetidas no texto."""
    frases = [_chave_frase(f) for f in re.split(r"(?<=[.!?])\s+|\n+", texto)]
    frases = [f for f in frases if len(f.split()) >= 5]
    return len(frases) - len(set(frases))


def remover_repeticoes(texto: str) -> str:
    """Mantém só a primeira ocorrência de cada frase repetida (laços do modelo)."""
    vistas: set[str] = set()
    paragrafos = []
    for paragrafo in texto.split("\n"):
        partes = re.split(r"(?<=[.!?])\s+", paragrafo)
        mantidas = []
        for frase in partes:
            chave = _chave_frase(frase)
            if len(chave.split()) >= 5 and chave in vistas:
                continue
            vistas.add(chave)
            mantidas.append(frase)
        if mantidas or not paragrafo.strip():
            paragrafos.append(" ".join(mantidas))
    return re.sub(r"\n{3,}", "\n\n", "\n".join(paragrafos)).strip()


def cortar_frase_incompleta(texto: str) -> str:
    """Se o limite de tokens cortou a última frase, remove o pedaço cortado."""
    texto = texto.rstrip()
    if not texto or texto[-1] in ".!?:)`*\"»" or texto.endswith("```"):
        return texto
    corte = max(texto.rfind(". "), texto.rfind(".\n"), texto.rfind("? "), texto.rfind("?\n"),
                texto.rfind("! "), texto.rfind("!\n"))
    return texto[: corte + 1].rstrip() if corte > len(texto) * 0.5 else texto


def remover_blocos_de_codigo(texto: str) -> str:
    return re.sub(r"```.*?(?:```|$)", "", texto, flags=re.DOTALL).strip()


def encontrar_problemas(texto: str, exigencias: Exigencias) -> list[str]:
    problemas: list[str] = []
    limpo = texto.strip()
    if not limpo:
        return ["A resposta veio vazia."]
    norm = _normaliza(limpo)

    if len(limpo) > exigencias.max_caracteres:
        problemas.append(
            f"A resposta tem {len(limpo)} caracteres; reescreva com no máximo "
            f"{exigencias.max_caracteres // 7} palavras, mantendo só o essencial."
        )
    if _CODIGO_OUTRA_LINGUAGEM.search(limpo):
        problemas.append("Há código em outra linguagem: use apenas Java ou nenhuma linguagem.")
    if exigencias.sem_codigo and "```" in limpo:
        problemas.append(
            "Não escreva blocos de código nem diagramas: o sistema já exibe o material "
            "verificado; explique com palavras."
        )
    for expressao, mensagem in _AFIRMACOES_ERRADAS:
        if re.search(expressao, norm):
            problemas.append(mensagem)
    if contar_repeticoes(limpo) >= 2:
        problemas.append("A resposta repete as mesmas frases; escreva cada ideia uma única vez.")
    if len(_INGLES.findall(limpo)) > 12:
        problemas.append("Responda em português do Brasil.")
    for alternativas in exigencias.termos_obrigatorios:
        if not any(_normaliza(t) in norm for t in alternativas):
            problemas.append(exigencias.descricao_termos or f"Mencione {alternativas[0]}.")
            break
    return problemas


def corrigir_mecanicamente(texto: str, exigencias: Exigencias) -> str:
    texto = remover_meta_revisao(texto)
    if exigencias.sem_codigo:
        texto = remover_blocos_de_codigo(texto)
    return cortar_frase_incompleta(remover_repeticoes(remover_frases_erradas(texto)))


def premissas_falsas(pergunta: str) -> list[str]:
    """Correções a fazer quando a própria pergunta traz uma afirmação errada."""
    norm = _normaliza(pergunta)
    return [mensagem for expressao, mensagem in _AFIRMACOES_ERRADAS[:-1] if re.search(expressao, norm)]


class ValidadorDeterministico:
    """Guardrail de Task do CrewAI: devolve (aprovado, texto_ou_feedback)."""

    def __init__(self, exigencias: Exigencias) -> None:
        self.exigencias = exigencias
        self.tentativas = 0
        self.problemas_por_tentativa: list[list[str]] = []

    # Sem anotação de retorno: o CrewAI só aceita Tuple[bool, Any] não adiado,
    # e este módulo usa `from __future__ import annotations`. Retorna (bool, str).
    def validar(self, saida):
        texto = remover_meta_revisao(getattr(saida, "raw", str(saida)))
        problemas = encontrar_problemas(texto, self.exigencias)
        self.problemas_por_tentativa.append(problemas)
        self.tentativas += 1
        if problemas and self.tentativas == 1:
            return False, (
                "Sua resposta tem problemas. Escreva uma nova versão completa, corrigindo:\n- "
                + "\n- ".join(problemas)
            )
        return True, corrigir_mecanicamente(texto, self.exigencias) or texto


def ler_veredito(texto: str) -> tuple[bool | None, list[str]]:
    """Interpreta a saída do Guardião: (aprovado, problemas).

    None indica saída fora do formato; nesse caso o fluxo não reescreve nada
    (as verificações determinísticas já foram aplicadas).
    """
    norm = _normaliza(texto)
    problemas = [
        re.sub(r"^\s*(?:[-*•]|\d+[.)])\s*", "", linha).strip()
        for linha in texto.splitlines()
        if re.match(r"^\s*(?:[-*•]|\d+[.)])\s+\S", linha)
    ]
    if "reprovado" in norm:
        return False, problemas[:3]
    if "aprovado" in norm:
        return True, []
    return None, []


# Trechos usados como exemplo no prompt do Guardião: ele às vezes os copia.
_EXEMPLOS_DO_PROMPT = {
    "o concreteproduct sobrescreve o metodo de criacao",
    "o simple factory e um dos padroes gof",
}


def problemas_fundamentados(problemas: list[str], resposta: str) -> tuple[list[str], list[str]]:
    """Separa os problemas do Guardião que citam um trecho real da resposta.

    No teste real (04/11), o Guardião de 3B reprovou as 8 respostas com
    problemas inventados ("o Factory Method não é GoF"), e a reescrita copiou
    essas falsidades. Por isso cada problema precisa citar, entre aspas, um
    trecho que exista de fato na resposta, e não pode contradizer a
    referência. Os demais são descartados (e registrados na memória).
    """
    alvo = re.sub(r"\s+", " ", _normaliza(resposta))
    aceitos, descartados = [], []
    for problema in problemas:
        trechos = [t for t in re.findall(r"[\"“«']([^\"”»']+)[\"”»']", problema) if len(t.split()) >= 3]
        citado = any(re.sub(r"\s+", " ", _normaliza(t)).strip(" .") in alvo for t in trechos)
        # Precisa dizer o que está errado, além de citar (só a citação não é problema).
        resto = re.sub(r"[\"“«'][^\"”»']*[\"”»']", "", problema)
        explicado = len(re.findall(r"\w+", resto)) >= 4
        copiado_do_prompt = any(_normaliza(t) in _EXEMPLOS_DO_PROMPT for t in trechos)
        citado = citado and explicado and not copiado_do_prompt
        contradiz = bool(re.search(_FM_NAO_GOF, _normaliza(problema)))
        (aceitos if citado and not contradiz else descartados).append(problema)
    return aceitos, descartados


def garantir_pergunta_final(texto: str, pergunta_padrao: str) -> str:
    """Toda resposta termina convidando o estudante a continuar."""
    final = texto.rstrip()[-400:]
    if "?" in final:
        return texto.rstrip()
    return f"{texto.rstrip()}\n\n{pergunta_padrao}"
