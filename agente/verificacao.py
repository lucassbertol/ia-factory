"""Verificações determinísticas das respostas (guardrails do CrewAI).

Cada tarefa de um agente autor recebe um ValidadorDeterministico como
`guardrail`. Na primeira tentativa, se houver problema objetivo (código em
outra linguagem, papéis trocados, resposta longa demais...), o CrewAI devolve a
lista de problemas ao próprio agente e pede uma nova versão. Na segunda
tentativa o validador não reprova mais: aplica correções mecânicas (remove
blocos de código, rótulos de meta-revisão) e libera o texto. Assim o tempo de
resposta fica limitado. A decisão final do fluxo ainda bloqueia texto com
problemas remanescentes, mesmo que o Guardião o aprove. Na reescrita pedida
pelo Guardião não há retry adicional: aplica-se a limpeza e depois a validação final.

As regras cobrem erros que de fato apareceram nas evidências de teste com o
qwen2.5:3b (ex.: "ConcreteProduct sobrescreve o factory method", resposta com
código C#, "o Factory Method é confundido com o Factory Method").
"""

from __future__ import annotations

import json
import re
from difflib import SequenceMatcher
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
    # Interface web, 04/11: "O código de configuração (como no main) não precisa
    # mudar" ao adicionar um produto. O main escolhe o ConcreteCreator e muda.
    (r"\b(?:main|codigo de configuracao)(?:\s*\([^)]*\))?\s+(?:tambem\s+)?(?:nao|nunca)\s+"
     r"(?:precisa|precisara|vai precisar|tem que|necessita|sera|e)\w*\s+(?:de\s+)?(?:ser\s+)?"
     r"(?:mud|alter|modific|mexid|toc)\w*"
     r"|\bnem o (?:main|codigo de configuracao) precisa\w* (?:de )?(?:ser )?(?:mud|alter|modific)\w*"
     r"|\bsem (?:precisar |ter que )?(?:mudar|alterar|modificar|mexer)(?: em| no)? (?:o )?(?:main|codigo de configuracao)\b",
     "Ao adicionar um produto, o código de configuração (o main) muda para escolher o novo "
     "ConcreteCreator; o que não muda é o Creator e o código que usa o contrato Product."),
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
    # (expressão, mensagem): conteúdo que não deve aparecer neste turno; na
    # segunda tentativa, as frases que casam são removidas.
    proibidos: list[tuple[str, str]] = field(default_factory=list)
    # Nomes do gabarito que o estudante ainda não citou. Na avaliação de uma
    # tentativa, citar mais de `max_reservados` deles é entregar a solução.
    reservados: list[str] = field(default_factory=list)
    max_reservados: int = 2
    # O que o estudante escreveu no exercício. Quando preenchido, frases que lhe
    # atribuem um erro ou uma definição sobre algo que ele não citou são barradas.
    fala_estudante: str = ""
    # Respostas já dadas pelo sistema neste exercício: repetir uma delas é ignorar
    # a tentativa nova.
    respostas_anteriores: list[str] = field(default_factory=list)
    # A avaliação verificada não achou equívoco: o texto não pode apontar erros.
    sem_equivocos: bool = False


# Termos que o Inquiridor pode atribuir ao estudante sem que ele os tenha usado.
_TERMOS_TENTATIVA = (
    r"concrete ?products?", r"concrete ?creators?", r"creator", r"product", r"factory method",
    r"metodo fabrica", r"emitir", r"criar\w+", r"if", r"switch", r"static", r"subclasses?",
    r"interface", r"heranca", r"sobrescr\w*",
)
_ATRIBUI_ERRO = re.compile(r"\b(?:equivoc\w*|erro|errou|errad[oa]|incorret\w*|engano)\b")
_ATRIBUI_FALA = re.compile(
    r"\b(?:voce|vc)\s+(?:\w+\s+)?(?:descreveu|mencionou|disse|definiu|colocou|escreveu|usou|"
    r"propos|sugeriu|citou|indicou|identificou|confundiu|esqueceu)\b"
    r"|\b(?:sua|na sua|da sua) (?:definicao|descricao|resposta (?:sobre|para) o)"
)


def frases_com_equivoco(texto: str) -> list[str]:
    """Frases que afirmam um erro ou pedem ajuste (sem negação nem tom de alerta)."""
    encontradas = []
    for frase in re.split(r"(?<=[.!?])\s+|\n+", texto):
        norm = _normaliza(frase)
        # Teste web de 04/11: "Não está correto." para uma resposta certa.
        afirma = (_ATRIBUI_ERRO.search(norm) or re.search(r"\b(?:ajust|corrig)\w*", norm)
                  or re.search(r"\bnao (?:esta|e|eh|ficou|parece) (?:muito |bem |totalmente )?(?:corret|cert)\w*"
                               r"|\bnao (?:e|eh) bem (?:isso|assim)", norm))
        negada = re.search(r"\b(?:nao ha|sem|nenhum|nao (?:tem|houve|cometeu|precisa))\b"
                           r"|\bnao (?:esta|e|eh) (?:errad|incorret)", norm)
        alerta = re.search(r"\b(?:erros? comu\w*|cuidado|evite|atencao)\b", norm)
        if afirma and not negada and not alerta:
            encontradas.append(frase.strip())
    return encontradas


def repete_resposta(texto: str, anterior: str) -> bool:
    """Texto quase igual a uma resposta anterior (cópia do histórico)."""
    a, b = _chave_frase(texto), _chave_frase(anterior)
    # Repetir só uma pergunta curta ("Quem seria o Creator?") não é cópia.
    if len(a.split()) < 15 or len(b.split()) < 15:
        return False
    if SequenceMatcher(None, a, b).ratio() >= 0.75:
        return True
    frases = lambda t: {_chave_frase(f) for f in re.split(r"(?<=[.!?])\s+", t)
                        if len(_chave_frase(f).split()) >= 6}
    comuns = frases(texto) & frases(anterior)
    return len(comuns) >= 2 and len(comuns) >= len(frases(texto)) / 2


def _termos(trecho: str) -> list[str]:
    return [t for t in _TERMOS_TENTATIVA if re.search(rf"\b{t}\b", trecho)]


def frases_atribuidas(texto: str, fala_estudante: str) -> list[str]:
    """Frases que dizem que o estudante errou ou definiu algo que ele não escreveu.

    Teste web de 04/11: à tentativa "o product seria o recibo", o Inquiridor
    respondeu "há um equívoco na definição dos ConcreteProducts e do Creator" e
    falou de um if em emitir() "que você descreveu": nada disso foi escrito.
    Cada oração que acusa um erro ou cita uma fala do estudante precisa tratar de
    pelo menos um termo que ele usou.
    """
    fala = _normaliza(fala_estudante)
    encontradas = []
    for frase in re.split(r"(?<=[.!?])\s+|\n+", texto):
        norm = _normaliza(frase)
        if re.search(r"\b(?:erros? comu\w*|cuidado|evite|atencao)\b", norm):
            continue
        for oracao in re.split(r"[,;:]|\b(?:mas|porem|no entanto|entretanto)\b", norm):
            negada = re.search(r"\b(?:nao ha|sem|nenhum|nao (?:tem|houve|cometeu))\b", oracao)
            atribui = (_ATRIBUI_ERRO.search(oracao) and not negada) or _ATRIBUI_FALA.search(oracao)
            termos = _termos(oracao)
            if atribui and termos and not any(re.search(rf"\b{t}\b", fala) for t in termos):
                encontradas.append(frase.strip())
                break
    return encontradas


_PAPEIS = {"concreteproduct", "concreteproducts", "concretecreator", "concretecreators",
           "factorymethod", "simplefactory", "abstractfactory", "gof"}


def nomes_reservados(gabarito: str, ja_citado: str) -> list[str]:
    """Classes e métodos do gabarito (ReciboPdf, criarRecibo...) ainda não citados
    pelo estudante nem pelo enunciado. Nomes de papéis do padrão não contam."""
    citado = _normaliza(ja_citado)
    nomes = re.findall(r"\b(?:[A-Z][a-z0-9]+(?:[A-Z][a-z0-9]*)+|[a-z]+[A-Z]\w*)\b", gabarito)
    return [n for n in dict.fromkeys(nomes)
            if n.lower() not in _PAPEIS and not re.search(rf"\b{re.escape(n.lower())}\b", citado)]


def _reservados_citados(texto: str, reservados: list[str]) -> list[str]:
    norm = _normaliza(texto)
    return [n for n in reservados if re.search(rf"\b{re.escape(n.lower())}\b", norm)]


def limitar_reservados(texto: str, reservados: list[str], maximo: int) -> str:
    """Remove, do fim para o começo, frases que revelam nomes do gabarito."""
    if len(_reservados_citados(texto, reservados)) <= maximo:
        return texto
    linhas = [re.split(r"(?<=[.!?])\s+", linha) for linha in texto.splitlines()]
    for i in range(len(linhas) - 1, -1, -1):
        for j in range(len(linhas[i]) - 1, -1, -1):
            if _reservados_citados(linhas[i][j], reservados):
                linhas[i][j] = ""
                atual = "\n".join(" ".join(f for f in linha if f) for linha in linhas)
                if len(_reservados_citados(atual, reservados)) <= maximo:
                    return re.sub(r"\n{3,}", "\n\n", atual).strip()
    return "\n".join(" ".join(f for f in linha if f) for linha in linhas).strip()


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
    # Eco da tentativa ("**Estudante:** Product seria Recibo."), teste web de 04/11.
    r"|(?:estudante|aluno|tentativa(?: do estudante)?|resposta do estudante|sua resposta|sua tentativa)\**\s*:.*"
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
            r"pergunta do inquiridor|pergunta para o estudante|pergunta guia|gabarito|"
            r"avalia[cç][aã]o|feedback)\s*\**\s*:\**\s*",
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
    r"|aqui esta uma pergunta"
    r"|\badicionei (?:a|uma|o|um)\b"
    r"|sistema multiagente|\bos agentes\b|\breferencia local\b"
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
    """Retira os blocos de código e o título que só os anunciava."""
    return re.sub(
        r"(?:^[ \t]*(?:#{1,6}[ \t]+[^\n]*|\*\*[^*\n]{1,80}\*\*:?)[ \t]*\n\s*)?```.*?(?:```|\Z)",
        "", texto, flags=re.DOTALL | re.MULTILINE,
    ).strip()


_TITULO = re.compile(r"^\s*(?:#{1,6}\s+\S.*|\*\*[^*\n]{1,80}\*\*\s*:?)\s*$")


def remover_titulos_vazios(texto: str) -> str:
    """Remove títulos que ficaram sem conteúdo (ex.: "### Implementação em Java"
    depois que o bloco de código do Tutor foi retirado, teste web de 04/11)."""
    linhas = texto.splitlines()
    mantidas: list[str] = []
    for i, linha in enumerate(linhas):
        if _TITULO.match(linha):
            seguinte = next((l for l in linhas[i + 1:] if l.strip()), "")
            if not seguinte or _TITULO.match(seguinte):
                continue
        mantidas.append(linha)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(mantidas)).strip()


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
    for expressao, mensagem in exigencias.proibidos:
        if re.search(expressao, norm):
            problemas.append(mensagem)
    if exigencias.sem_equivocos and frases_com_equivoco(limpo):
        problemas.append(
            "A avaliação verificada não encontrou nenhum equívoco na tentativa: não aponte "
            "erros (\"" + frases_com_equivoco(limpo)[0][:100] + "\"). Confirme o que está certo."
        )
    if any(repete_resposta(limpo, anterior) for anterior in exigencias.respostas_anteriores):
        problemas.append(
            "Você repetiu uma resposta que já deu neste exercício. Leia a TENTATIVA ATUAL do "
            "estudante e avalie o que ela traz de novo; não peça partes que ele já respondeu."
        )
    if exigencias.fala_estudante and frases_atribuidas(limpo, exigencias.fala_estudante):
        problemas.append(
            "Você atribuiu ao estudante algo que ele não escreveu (\""
            + frases_atribuidas(limpo, exigencias.fala_estudante)[0][:120]
            + "\"). Avalie só o que está na mensagem dele; se ele respondeu uma parte, "
            "confirme-a e pergunte sobre a próxima."
        )
    revelados = _reservados_citados(limpo, exigencias.reservados)
    if len(revelados) > exigencias.max_reservados:
        problemas.append(
            "Não entregue a solução do exercício (você citou " + ", ".join(revelados)
            + "): diga o que está certo e faça uma pergunta guia sobre a próxima parte."
        )
    for alternativas in exigencias.termos_obrigatorios:
        if not any(_normaliza(t) in norm for t in alternativas):
            problemas.append(exigencias.descricao_termos or f"Mencione {alternativas[0]}.")
            break
    return problemas


def _remover_frases(texto: str, expressoes: list[str]) -> str:
    linhas = []
    for linha in texto.splitlines():
        frases = re.split(r"(?<=[.!?])\s+", linha)
        mantidas = [f for f in frases if not any(re.search(e, _normaliza(f)) for e in expressoes)]
        if mantidas or not linha.strip():
            linhas.append(" ".join(mantidas))
    return "\n".join(linhas).strip()


def remover_introducoes_penduradas(texto: str) -> str:
    """Remove parágrafos que anunciam algo ("a saída será:") sem nada depois."""
    paragrafos = texto.split("\n\n")
    mantidos = []
    for i, paragrafo in enumerate(paragrafos):
        seguinte = paragrafos[i + 1].lstrip() if i + 1 < len(paragrafos) else ""
        anuncia = paragrafo.rstrip().endswith(":") and "\n" not in paragrafo.strip()
        if anuncia and not re.match(r"(?:[-*•]|\d+[.)]|```|\|)", seguinte):
            continue
        mantidos.append(paragrafo)
    return "\n\n".join(mantidos)


def limitar_tamanho(texto: str, maximo: int) -> str:
    """Corta parágrafos excedentes, mantendo a pergunta final ao estudante."""
    if len(texto) <= maximo:
        return texto
    paragrafos = texto.split("\n\n")
    final = paragrafos[-1] if paragrafos[-1].rstrip().endswith("?") else ""
    corpo, total = [], len(final)
    for paragrafo in paragrafos[:-1] if final else paragrafos:
        if total + len(paragrafo) > maximo and corpo:
            break
        corpo.append(paragrafo)
        total += len(paragrafo) + 2
    return "\n\n".join(corpo + ([final] if final else []))


def corrigir_mecanicamente(texto: str, exigencias: Exigencias) -> str:
    texto = remover_meta_revisao(texto)
    if exigencias.sem_codigo:
        texto = remover_blocos_de_codigo(texto)
    texto = remover_frases_erradas(texto)
    if exigencias.proibidos:
        texto = _remover_frases(texto, [e for e, _ in exigencias.proibidos])
    if exigencias.reservados:
        texto = limitar_reservados(texto, exigencias.reservados, exigencias.max_reservados)
    if exigencias.sem_equivocos:
        for frase in frases_com_equivoco(texto):
            texto = texto.replace(frase, "")
    if exigencias.fala_estudante:
        for frase in frases_atribuidas(texto, exigencias.fala_estudante):
            texto = texto.replace(frase, "")
        texto = "\n".join(re.sub(r"[ \t]{2,}", " ", linha).rstrip() for linha in texto.splitlines())
    texto = remover_introducoes_penduradas(remover_titulos_vazios(remover_repeticoes(texto)))
    texto = remover_titulos_vazios(texto)
    return cortar_frase_incompleta(limitar_tamanho(texto, exigencias.max_caracteres))


def premissas_falsas(pergunta: str) -> list[str]:
    """Correções a fazer quando a própria pergunta traz uma afirmação errada."""
    norm = _normaliza(pergunta)
    return [mensagem for expressao, mensagem in _AFIRMACOES_ERRADAS[:-1] if re.search(expressao, norm)]


class ValidadorDeterministico:
    """Guardrail de Task do CrewAI: devolve (aprovado, texto_ou_feedback)."""

    def __init__(self, exigencias: Exigencias, permitir_retentativa: bool = True) -> None:
        self.exigencias = exigencias
        self.permitir_retentativa = permitir_retentativa
        self.tentativas = 0
        self.problemas_por_tentativa: list[list[str]] = []

    # Sem anotação de retorno: o CrewAI só aceita Tuple[bool, Any] não adiado,
    # e este módulo usa `from __future__ import annotations`. Retorna (bool, str).
    def validar(self, saida):
        texto = remover_meta_revisao(getattr(saida, "raw", str(saida)))
        problemas = encontrar_problemas(texto, self.exigencias)
        self.problemas_por_tentativa.append(problemas)
        self.tentativas += 1
        if problemas and self.tentativas == 1 and self.permitir_retentativa:
            return False, (
                "Sua resposta tem problemas. Escreva uma nova versão completa, corrigindo:\n- "
                + "\n- ".join(problemas)
            )
        return True, corrigir_mecanicamente(texto, self.exigencias) or texto


def avaliar_revisao(texto: str, textos: dict[str, str], pergunta: str, referencia: str) -> dict:
    """Valida o contrato e as citações; não substitui o julgamento semântico."""
    resultado = {"veredito": "INCONCLUSIVO", "problemas": [],
                 "problemas_descartados": [], "motivo": "Formato de revisão inválido."}
    cercado = re.fullmatch(r"```(?:json)?\s*\n(.*?)\n```", texto.strip(), re.DOTALL)
    if cercado:
        texto = cercado.group(1)

    def sem_chaves_duplicadas(pares):
        objeto = {}
        for chave, valor in pares:
            if chave in objeto:
                raise ValueError("Chave JSON duplicada")
            objeto[chave] = valor
        return objeto

    try:
        dados = json.loads(texto, object_pairs_hook=sem_chaves_duplicadas)
    except (ValueError, TypeError):
        return resultado
    if not isinstance(dados, dict) or set(dados) != {"veredito", "problemas"}:
        return resultado
    status, problemas = dados["veredito"], dados["problemas"]
    if status not in ("APROVADO", "REPROVADO", "INCONCLUSIVO") or not isinstance(problemas, list):
        return resultado
    if len(problemas) > 3 or (status != "REPROVADO" and problemas):
        return resultado
    if status == "APROVADO":
        return {**resultado, "veredito": "APROVADO", "motivo": ""}
    if status == "INCONCLUSIVO" or not problemas:
        return {**resultado, "motivo": "O Guardião não apresentou uma decisão fundamentada."}

    def citado(trecho, origem, minimo):
        return (isinstance(trecho, str) and len(trecho.split()) >= minimo
                and " ".join(_normaliza(trecho).split()) in " ".join(_normaliza(origem).split()))

    aceitos, descartados = [], []
    for problema in problemas:
        valido = isinstance(problema, dict)
        if valido:
            autor = problema.get("autor")
            correcao = problema.get("correcao")
            valido = (isinstance(autor, str) and autor in textos
                      and isinstance(correcao, str) and len(correcao.split()) >= 4
                      and not re.search(_FM_NAO_GOF, _normaliza(correcao)))
        if valido:
            if problema.get("tipo") == "erro":
                valido = (citado(problema.get("trecho"), textos[autor], 3)
                          and citado(problema.get("referencia"), referencia, 4))
            elif problema.get("tipo") == "incompleto":
                valido = citado(problema.get("pedido"), pergunta, 2)
            else:
                valido = False
        (aceitos if valido else descartados).append(problema)
    # Uma crítica inventada invalida a revisão, sem orientar reescritas parciais.
    return {"veredito": "INCONCLUSIVO" if descartados else "REPROVADO",
            "problemas": aceitos, "problemas_descartados": descartados,
            "motivo": "Crítica sem evidência verificável." if descartados else ""}


def garantir_pergunta_final(texto: str, pergunta_padrao: str) -> str:
    """Toda resposta termina convidando o estudante a continuar."""
    final = texto.rstrip()[-400:]
    if "?" in final:
        return texto.rstrip()
    return f"{texto.rstrip()}\n\n{pergunta_padrao}"
