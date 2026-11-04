"""Roteador de intenções (determinístico) e barreiras anti-alucinação.

Escolhemos regras em vez de pedir ao modelo de 3B que classifique a pergunta:
são instantâneas, previsíveis e testáveis (tests/test_roteador.py). O custo é a
rigidez diante de formulações muito livres; erros de digitação nas palavras que
decidem o destino são corrigidos antes (normalizar_pergunta).

Ordem de decisão:
  1. Barreiras (detectar_barreira): saudação, invenção de padrão, padrão
     inexistente, outro padrão do GoF e solução pronta. Respondidas sem o modelo.
  2. Encerramento e tentativas identificáveis do exercício em andamento.
  3. Pedidos explícitos: exercício, uso incorreto, comparação, seleção.
  4. Continuações curtas ("sim", "e por quê?") usando o estado da sessão.
  5. Exemplo, diagnóstico, fechamento, conceito.
  6. Sem vocabulário do domínio: fora de escopo.
"""

from __future__ import annotations

from dataclasses import dataclass

import unicodedata
import re


def _normaliza(texto: str) -> str:
    """Remove acentos e deixa minusculo para comparacao robusta."""
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


# Palavras que decidem o roteamento. Um erro de digitação nelas ("exerício",
# "factory metod") mandava o pedido para o destino errado: o pedido de
# exercício caía em "conceito" e o Tutor improvisava um exemplo (teste na
# interface web, 04/11). A ordem desempata: "metod" vira "method".
_PALAVRAS_CHAVE = (
    "exercicio", "exercicios", "exemplo", "exemplos", "desafio", "desafios",
    "atividade", "atividades", "praticar", "factory", "method", "metodo",
    "padrao", "explique", "explicar", "diferenca", "comparacao", "comparar",
    "confundido", "encerrar", "cancelar", "abstract", "simple", "strategy",
    "template", "participantes", "incorreto", "equivocado", "conceito",
)
# Palavras reais próximas de uma palavra-chave, que não devem ser trocadas.
_PALAVRAS_REAIS = {"exercito", "exercer", "exerceu", "exemplar", "exemplares", "metade",
                   "padrinho", "simples", "factor", "fabrico", "comparo", "explico",
                   "explica", "explicou", "conceitos", "atividades"}


def _distancia(a: str, b: str, limite: int) -> int:
    """Distância de edição com transposição (Damerau restrita), com corte."""
    if abs(len(a) - len(b)) > limite:
        return limite + 1
    anterior2: list[int] = []
    anterior = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        atual = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            atual[j] = min(anterior[j] + 1, atual[j - 1] + 1, anterior[j - 1] + (ca != cb))
            if i > 1 and j > 1 and ca == b[j - 2] and a[i - 2] == cb:
                atual[j] = min(atual[j], anterior2[j - 2] + 1)
        if min(atual) > limite:
            return limite + 1
        anterior2, anterior = anterior, atual
    return anterior[-1]


def _corrigir_palavra(palavra: str) -> str:
    if len(palavra) < 5 or palavra in _PALAVRAS_CHAVE or palavra in _PALAVRAS_REAIS:
        return palavra
    for chave in _PALAVRAS_CHAVE:
        # Mesma inicial; 1 erro em palavras curtas, 2 nas de 9 letras ou mais.
        limite = 2 if len(chave) >= 9 else 1
        if chave[0] == palavra[0] and _distancia(palavra, chave, limite) <= limite:
            return chave
    return palavra


def normalizar_pergunta(texto: str) -> str:
    """Minúsculas, sem acentos, espaços simples e palavras-chave com erro de
    digitação corrigidas ("me de um exerício" -> "me de um exercicio")."""
    p = " ".join(_normaliza(texto).split())
    return re.sub(r"[a-z]+", lambda m: _corrigir_palavra(m.group(0)), p)


# Intencoes respondidas sem chamar o modelo (texto deterministico).
INTENCOES_SEM_MODELO = {
    "saudacao", "inventicao", "padrao_desconhecido", "outro_padrao",
    "solucao_pronta", "fora_de_escopo",
}


@dataclass
class Intencao:
    """Classificacao da intencao da pergunta do estudante."""

    tipo: str
    confianca: float
    detalhe: str = ""
    usar_contexto: bool = False


_SAUDACOES = {
    "oi", "ola", "oie", "opa", "bom dia", "boa tarde", "boa noite", "e ai", "eai",
    "hello", "hi", "hey", "tudo bem", "oi tudo bem", "ola tudo bem", "salve",
    "ajuda", "help", "menu", "comandos", "o que voce faz", "o que voce sabe fazer",
    "quem e voce", "como voce funciona", "como funciona isso", "como usar",
    "o que posso perguntar", "comecar", "vamos comecar", "inicio",
}

_INVENCAO = re.compile(
    r"\b(?:invent\w*|imagin\w*|finj\w*|faca de conta|elabor\w*|bol\w*|"
    r"cri(?:e|ar|a|ou))\s+(?:para mim\s+|pra mim\s+)?(?:um|uma|o|seu|meu|novo)?\s*"
    r"(?:novo\s+)?padr(?:ao|oes)\b"
    r"|\bpadr(?:ao|oes)\s+(?:ficticio|imaginario|inexistente|inventado|que nao existe)"
    r"|\binvent\w*\b.*\bpadr(?:ao|oes)\b"
)

_SOLUCAO_PRONTA = re.compile(
    r"\bcodigo\s+(?:pronto|completo|inteiro|final)\b"
    r"|\b(?:solucao|resolucao|implementacao)\s+(?:pronta|completa|inteira|final)\b"
    r"|\b(?:faca|faz|fazer|termine|termina|complete)\s+(?:o |a )?(?:meu|minha)\s+"
    r"(?:trabalho|tarefa|lista|atividade|exercicio|projeto)\b"
    r"|\b(?:resolva|resolve|resolver)\s+(?:o|a|meu|minha|esse|essa|este|esta)\s+"
    r"(?:trabalho|tarefa|lista|atividade|exercicio|projeto)\b"
    r"|\b(?:resolva|resolve|faca|faz)\s+(?:isso\s+|tudo\s+)?(?:pra|para) mim\b"
    r"|\b(?:pra|para) eu (?:entregar|copiar|colar)\b"
    r"|\bcopi(?:e|ar) e col(?:e|ar)\b|\bctrl\s*\+?\s*[cv]\b"
    r"|\b(?:sistema|projeto|programa|aplicacao|app)\s+(?:completo|completa|inteiro|inteira)\b"
    r"|\b(?:me )?entreg\w* (?:o |a )?(?:codigo|resposta|solucao)\b"
    r"|\bgabarito\b"
)

_PEDE_RESPOSTA_EXERCICIO = re.compile(
    r"\b(?:me )?(?:de|da|diga|diz|fala|fale|passa|passe|mostre|mostra)\s+"
    r"(?:logo\s+)?a\s+resposta\b|\bqual (?:e )?a resposta\b"
)

_PREENCHIMENTO_APOS_PADRAO = {
    "chamado", "chamada", "denominado", "denominada", "conhecido", "conhecida",
    "como", "gof", "criacional",
}


def _sem_acento(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def extrair_nomes_de_padrao(pergunta: str) -> list[tuple[str, str]]:
    """Encontra nomes citados como "padrão X" ou "X pattern".

    Devolve pares (nome normalizado, nome como foi escrito). Só considera um
    nome desconhecido quando ele foi escrito com inicial maiúscula (nome
    próprio) ou é uma letra isolada, para não confundir "o padrão resolve"
    com um padrão chamado "resolve".
    """
    from .catalogo import NAO_SAO_NOMES, classificar_nome

    tokens = re.findall(r"[A-Za-z0-9][A-Za-z0-9\-]*", _sem_acento(pergunta))
    encontrados: list[tuple[str, str]] = []
    for i, token in enumerate(tokens):
        if token.lower() not in {"padrao", "pattern"}:
            continue
        j = i + 1
        while j < len(tokens):
            atual = tokens[j].lower()
            if atual in _PREENCHIMENTO_APOS_PADRAO:
                j += 1
            elif atual == "de" and j + 1 < len(tokens) and tokens[j + 1].lower() in {"projeto", "projetos", "nome"}:
                j += 2
            else:
                break
        nome: list[str] = []
        while j < len(tokens) and len(nome) < 3 and tokens[j].lower() not in NAO_SAO_NOMES:
            nome.append(tokens[j])
            j += 1
        if not nome:
            continue
        normalizado = " ".join(t.lower() for t in nome)
        tipo = classificar_nome(normalizado)
        if tipo == "desconhecido":
            # Reduz ao maior prefixo conhecido ("factory method em" -> conhecido).
            for k in range(len(nome) - 1, 0, -1):
                if classificar_nome(" ".join(t.lower() for t in nome[:k])) != "desconhecido":
                    tipo = "conhecido"
                    break
        proprio = nome[0][0].isupper() or (len(nome[0]) == 1 and nome[0].isalpha())
        if tipo == "desconhecido" and not proprio:
            continue
        encontrados.append((normalizado, " ".join(nome)))
    return encontrados


def detectar_barreira(pergunta: str, *, exercicio_pendente: bool = False) -> Intencao | None:
    """Pedidos que o sistema responde sem chamar o modelo (ou None)."""
    from .catalogo import classificar_nome

    p = " ".join(_normaliza(pergunta).split())
    curta = re.sub(r"[^\w\s]", "", p).strip()

    if curta in _SAUDACOES or (
        len(curta.split()) <= 4
        and re.match(r"^(?:oi|ola|oie|bom dia|boa tarde|boa noite|e ai|hello|hi|hey)\b", curta)
        and "factory" not in curta
    ):
        return Intencao("saudacao", 0.95, "saudação ou pedido de ajuda")

    if _INVENCAO.search(p):
        return Intencao("inventicao", 0.95, "pedido de invenção de padrão")

    pedido_pronto = _SOLUCAO_PRONTA.search(p)
    if pedido_pronto and "exemplo" in p and not re.search(
        r"solucao|pronto|entreg|trabalho|projeto|sistema|atividade|exercicio", p
    ):
        pedido_pronto = None  # "codigo completo do exemplo" e pedido de exemplo
    if pedido_pronto or (exercicio_pendente and _PEDE_RESPOSTA_EXERCICIO.search(p)):
        return Intencao("solucao_pronta", 0.95, "pedido de solução pronta")

    nomes = extrair_nomes_de_padrao(pergunta)
    for normalizado, original in nomes:
        if classificar_nome(normalizado) == "desconhecido":
            return Intencao("padrao_desconhecido", 0.9, original)

    menciona_fm = any(t in p for t in ("factory method", "metodo fabrica", "metodo de fabrica"))
    for normalizado, original in nomes:
        if classificar_nome(normalizado) == "outro" and not menciona_fm:
            return Intencao("outro_padrao", 0.85, original)
    return None


def detectar_nivel(pergunta: str) -> str:
    """Nível declarado pelo estudante na mensagem ("sou iniciante"), ou ""."""
    p = _normaliza(pergunta)
    padroes = {
        "iniciante": r"\b(?:sou|estou|nivel)\s+(?:um |uma )?(?:iniciante|basico|novato|leigo)\b",
        "intermediario": r"\b(?:sou|estou|nivel)\s+(?:um |uma )?intermediari[oa]\b",
        "avancado": r"\b(?:sou|estou|nivel)\s+(?:um |uma )?(?:avancad[oa]|experiente)\b",
    }
    for nivel, expr in padroes.items():
        if re.search(expr, p):
            return nivel
    return ""


_VOCABULARIO_PRATICA = (
    r"\b(?:products?|creators?|concret\w*|produtos?|criador\w*|recibos?\w*|emissor\w*|emitir|"
    r"html|pdf|pagamentos?|caixa\w*|pix|cartao|whats\w*|notificador\w*|notificac\w*|"
    r"seria|seriam|criaria|usaria|faria|colocaria|implement\w*|sobrescrev\w*|estend\w*|"
    r"extends|herd\w*|subclasses?|simple factory|static|estatic\w*)\b"
)
# Nomes do domínio dos três exercícios do banco.
_VOCABULARIO_EXERCICIOS = (
    r"\b(?:recibos?\w*|emissor\w*|emitir|html|pdf|pagamentos?|caixa\w*|pix|cartao|whats\w*|"
    r"notificador\w*|fabricapagamento)\b"
)
# Palavras típicas de quem está respondendo (sem vocabulário técnico):
# "Não existe", "Ela está errada", "Acho que é o Emissor".
_PALAVRAS_DE_RESPOSTA = (
    r"\b(?:sim|nao|acho|creio|seria|seriam|ela|ele|esta|certa|certo|errad\w*|existe|existem|"
    r"nenhum\w*|tem|teria|classe\w*|metodo\w*|interface|novo|nova|main|codigo)\b"
)
_DUVIDAS_NO_EXERCICIO = {
    "nao entendi", "como assim", "nao sei", "nao sei responder", "pode explicar melhor",
    "explica melhor", "me ajuda", "uma dica", "me da uma dica", "me de uma dica", "dica",
    "nao entendi a pergunta", "nao sei por onde comecar",
}
_PERGUNTA_DE_CONCEITO = (
    r"^(?:o que|oque|explique|explica|como funciona|qual (?:a|e a) diferenca|por que|porque|"
    r"pra que|para que|me (?:explique|explica|de um exemplo|mostre))\b"
)


def classificar_intencao(
    pergunta: str,
    *,
    ultima_intencao: str = "",
    exercicio_pendente: bool = False,
) -> Intencao:
    """Classifica o pedido, considerando a continuidade da sessao quando informada.

    As recusas tem prioridade. Pedidos explicitos de conceito/exemplo/pratica
    mantem seu destino; tentativas e continuacoes usam o estado pedagogico.
    """
    p = normalizar_pergunta(pergunta)

    def contem(frases: list[str]) -> bool:
        """Verifica se alguma frase (normalizada) esta contida no texto."""
        return any(_normaliza(f) in p for f in frases)

    # 1. Barreiras determinísticas: saudação, invenção, padrão inexistente,
    #    outro padrão e solução pronta. Nenhuma delas chama o modelo.
    barreira = detectar_barreira(pergunta, exercicio_pendente=exercicio_pendente)
    if barreira is not None:
        return barreira

    # Uma resposta a pratica nao deve ser confundida com um novo pedido de
    # exercicio so porque menciona a palavra "exercicio" ou contem codigo.
    if contem(["encerrar exercicio", "encerrar o exercicio", "cancelar exercicio",
               "cancelar o exercicio", "desistir do exercicio"]):
        return Intencao("fechamento", 0.95, "encerramento explicito da pratica")

    tentativa = re.sub(r"^voltando (?:ao|para o) exercicio\s*[,.:;-]?\s*", "", p)
    if exercicio_pendente and re.match(
        r"^(?:minha (?:resposta|tentativa|implementacao)\b|meu codigo\b|tentei\b|"
        r"agora eu\b|eu usaria\b|eu faria\b|```|(?:public |abstract )?class\s)", tentativa
    ):
        return Intencao("avaliacao", 0.9, "tentativa identificavel da atividade", usar_contexto=True)

    referencia_anterior = contem([
        "exemplo anterior", "codigo anterior", "resposta anterior", "exercicio anterior",
        "neste exemplo", "nesse exemplo", "neste codigo", "nesse codigo",
        "neste exercicio", "nesse exercicio", "voce disse",
    ]) or bool(re.match(r"^e (?:quais|quando|como|por que)\b", p))

    pedido_pratica = (
        r"^(?:por favor[, ]+)?(?:(?:voce )?(?:pode|poderia)\s+)?(?:me\s+)?"
        r"(?:proponha|propor|crie|criar|sugira|sugerir|passe|passa|passar|de|da|dar|manda|mande|"
        r"traga|traz|gere|gera|elabore|quero|queria|gostaria de|peco|resolva)"
        r"\b.*\b(?:exercicio|desafio|atividade|quiz|tarefa)\b"
    )
    if (re.search(pedido_pratica, p)
            or contem(["me pergunte", "pergunta para mim", "quero praticar", "vamos praticar"])):
        return Intencao("exercicio", 0.85, "pedido de exercicio pratico")

    # Exercício em andamento: a mensagem é a resposta do estudante, sem precisar
    # de "Minha resposta:". Teste web de 04/11: respostas naturais ("Ela usou uma
    # Simple Factory", "Para HTML eu criaria ReciboHtml...") caíam em comparação
    # ou fora de escopo e o exercício se perdia. Ficam de fora só as perguntas e
    # os pedidos (conceito, exemplo, resumo, "não entendi"), tratados abaixo.
    contexto_de_pratica = exercicio_pendente
    curta = re.sub(r"[^\w\s]", "", p).strip()
    pergunta_conceito = re.match(_PERGUNTA_DE_CONCEITO, p) or re.search(
        r"\b(?:resum\w*|recapitul\w*|lembrar|fechamento|conclus\w*)\b", p) or (
        p.rstrip().endswith("?")
        and re.search(r"\b(?:diferenca|compar\w*|o que (?:e|eh|significa)|explic\w*|quando (?:usar|evitar))\b", p))
    pede_exemplo = re.search(
        r"^(?:me |quero |queria |gostaria de |pode |poderia |mostre|mostra|de |da )[^.?!]{0,30}\bexemplos?\b"
        r"|\b(?:exemplo|codigo) (?:em|de) java\b", p)
    duvida = curta in _DUVIDAS_NO_EXERCICIO
    # Pergunta geral ("Como o padrão costuma ser aplicado de forma errada?") não é
    # resposta, a menos que fale das classes do exercício.
    pergunta_geral = p.rstrip().endswith("?") and re.match(
        r"(?:e )?(?:como|qual|quais|quem|quando|onde|por que|porque|o que|pra que|para que|e se)\b", p
    ) and not re.search(_VOCABULARIO_EXERCICIOS, p)
    if contexto_de_pratica and pergunta_geral and not pergunta_conceito and re.search(r"\b(?:products?|creators?|concret\w*|participantes?)\b", p):
        # "Qual seria o Creator?": dúvida sobre o exercício, não pergunta solta.
        return Intencao("esclarecimento", 0.75, "duvida sobre a atividade em andamento", usar_contexto=True)
    if (contexto_de_pratica and not (pergunta_conceito or pede_exemplo or duvida or pergunta_geral)
            and re.search(_VOCABULARIO_PRATICA + "|" + _PALAVRAS_DE_RESPOSTA, p)):
        return Intencao("avaliacao", 0.75, "resposta ao exercicio em andamento", usar_contexto=True)

    # Pedidos expositivos vem antes de palavras como "exercicio" e "exemplo":
    # mencionar uma atividade nao significa responder a ela ou pedir outra.
    if contem(["uso incorreto", "uso equivocado", "forma errada", "forma incorreta",
               "aplicado errado", "aplicado incorretamente", "ma pratica", "antipadrao"]):
        return Intencao("uso_incorreto", 0.9, "erro, consequencia e correcao", referencia_anterior)
    if contem(["diferenca", "comparacao", "compare", "comparar", "confundido", "confundida",
               "mesmo que", "mesma coisa", "igual ao", "igual a", "e igual", "parecido com",
               "semelhante", "versus", " vs ", "simple factory", "abstract factory",
               "template method"]):
        return Intencao("comparacao", 0.9, "comparacao entre padroes", referencia_anterior)
    if (re.search(r"\bquando (?:nao )?(?:usar|utilizar|aplicar|adotar|evitar)\b", p)
            or contem(["melhor escolha", "deveria ser evitado", "deveria ser evitada",
                       "em que casos", "vale a pena", "quando devo usar", "quando devo evitar"])):
        return Intencao("selecao", 0.9, "quando usar e quando evitar", referencia_anterior)

    # Continuacoes elipticas precisam de contexto; nao basta tornar toda
    # mensagem desconhecida parte da aula (isso aceitaria assuntos alheios).
    if contexto_de_pratica and duvida:
        return Intencao("esclarecimento", 0.8, "duvida sobre a atividade em andamento", usar_contexto=True)
    if ultima_intencao and curta in {
        "sim", "nao", "entendi", "ok", "certo", "continue", "pode continuar",
        "e por que", "por que", "como assim", "nao sei", "e depois",
        "pode explicar melhor", "e quando devo usalo",
    }:
        # "Sim"/"Não" no exercício respondem à pergunta guia: são tentativa.
        tipo = ("avaliacao" if contexto_de_pratica and curta in {"sim", "nao"} else
                "esclarecimento" if contexto_de_pratica else ultima_intencao)
        if tipo not in {"conceito", "exemplo", "diagnostico", "avaliacao", "fechamento",
                        "selecao", "comparacao", "uso_incorreto", "esclarecimento"}:
            tipo = "conceito"
        return Intencao(tipo, 0.8, "continuidade do turno anterior", usar_contexto=True)


    # 3. Exemplo — pedido explícito de exemplo/código
    if contem(
        [
            "exemplo",
            "exemplos",
            "em java",
            "código java",
            "codigo java",
            "mostre o código",
            "mostre o codigo",
            "mostre como",
            "demonstre",
            "ilustre",
            "aplicação prática",
            "aplicacao pratica",
        ]
    ):
        return Intencao("exemplo", 0.85, "pedido de exemplo", referencia_anterior)

    # 4. Diagnóstico — dúvida, confusão, uso incorreto, comparação
    if contem(
        [
            "diagnóstico",
            "diagnostico",
            "conceito equivocado",
            "confundido",
            "confundo",
            "estou confuso",
            "não entendi",
            "nao entendi",
            "diferença",
            "diferenca",
            "comparação",
            "comparacao",
            "comparar",
            "errado",
            "errada",
            "incorreto",
            "incorreta",
            "má prática",
            "ma pratica",
            "antipadrão",
            "antipadrao",
            "simple factory",
            "abstract factory",
            "state",
            "strategy",
            "quando não usar",
            "quando nao usar",
            "limitações",
            "limitacoes",
        ]
    ):
        return Intencao("diagnostico", 0.8, "pedido de diagnostico da duvida", referencia_anterior)

    # 5. Fechamento
    if contem(
        [
            "lembrar",
            "fechamento",
            "antes de usar",
            "resumo",
            "resumir",
            "o que devo lembrar",
            "recapitular",
            "conclusão",
            "conclusao",
        ]
    ):
        return Intencao("fechamento", 0.8, "pedido de fechamento/resumo", referencia_anterior)

    # 6. Conceito — explicação do padrão
    if contem(
        [
            "o que é",
            "o que e",
            "explique",
            "explicar",
            "intencao",
            "intenção",
            "problema que resolve",
            "participantes",
            "estrutura",
            "consequencia",
            "consequência",
            "quando usar",
            "quando evitar",
            "para que serve",
            "como funciona",
            "definição",
            "definicao",
            "conceito",
        ]
    ):
        return Intencao("conceito", 0.85, "pedido de explicação do conceito", referencia_anterior)

    # 7. Vocabulário do domínio Factory Method (usado para detectar fora de escopo)
    vocabulario_dominio = [
        "factory method",
        "factory",
        "fabrica",
        "fábrica",
        "padrao de projeto",
        "padrão de projeto",
        "gof",
        "design pattern",
        "criacao",
        "criação",
        "instancia",
        "instância",
        "objeto",
        "classe",
        "produto",
        "concreto",
        "abstrato",
        "criador",
        "creator",
        "product",
        "concrete",
        "heranca",
        "herança",
        "polimorfismo",
        "encapsulamento",
        "acoplamento",
        "metodo",
        "método",
        "method",
        "poo",
        "orientacao a objetos",
        "orientação a objetos",
        "padrao",
        "pattern",
    ]

    def tem_vocabulario_dominio() -> bool:
        """Verifica se o texto contém palavras do domínio Factory Method."""
        return any(_normaliza(termo) in p for termo in vocabulario_dominio)

    # 7. Fora de escopo: não contém vocabulário do domínio e não foi
    # classificado como nenhuma intenção reconhecida acima.
    if not tem_vocabulario_dominio():
        return Intencao(
            "fora_de_escopo",
            0.7,
            "sem vocabulário do domínio Factory Method",
        )

    # 8. Default: conceito (tem vocabulário do domínio, mas não casou
    # nenhuma intenção específica acima).
    return Intencao("conceito", 0.5, "intenção não identificada com certeza")


def decidir_agentes(intencao: Intencao, pergunta: str = "") -> list[str]:
    """Decide quais agentes participam com base na intencao e na pergunta.

    A intencao primaria define o agente principal. Pedidos adicionais
    explicitos na mesma pergunta (ex.: "explique e de um exemplo") acrescentam
    os agentes correspondentes, mantendo a ordem pedagogica
    tutor -> exemplificador -> inquiridor -> guardiao.

    O Guardiao está sempre presente (revisão final anti-alucinação).
    """
    # Codigo e termos conceituais na tentativa sao dados a avaliar, nao
    # pedidos adicionais de exemplo ou de explicacao por outros agentes.
    if intencao.tipo in {"avaliacao", "esclarecimento"}:
        return ["inquiridor", "guardiao"]

    base_por_intencao = {
        "conceito": ["tutor"],
        "exemplo": ["exemplificador"],
        "exercicio": ["inquiridor"],
        "diagnostico": ["inquiridor"],
        "selecao": ["tutor"],
        "comparacao": ["tutor"],
        "uso_incorreto": ["exemplificador"],
        "fechamento": ["tutor"],
    }
    if intencao.tipo in INTENCOES_SEM_MODELO:
        return []
    base = base_por_intencao.get(intencao.tipo, ["tutor"])
    # Pedidos focados ficam com um unico agente autor: menos chamadas ao
    # modelo local e menos chance de respostas misturadas.
    if intencao.tipo in {"uso_incorreto", "comparacao", "selecao", "fechamento"}:
        return base + ["guardiao"]

    p = normalizar_pergunta(pergunta)

    def contem_termos(termos: list[str]) -> bool:
        return any(_normaliza(t) in p for t in termos)

    pede_exemplo = contem_termos(
        ["exemplo", "em java", "codigo java", "código java", "mostre o codigo"]
    )
    pede_diagnostico = contem_termos(
        [
            "errado",
            "errada",
            "incorreto",
            "incorreta",
            "confundido",
            "confundo",
            "diferenca",
            "diferença",
            "equivocado",
            "ma pratica",
            "má prática",
            "antipadrao",
            "antipadrão",
        ]
    )
    pede_exercicio = contem_termos(
        [
            "exercicio",
            "exercício",
            "proponha",
            "pratique",
            "praticar",
            "resolva",
            "desafio",
            "atividade",
            "quiz",
        ]
    )
    pede_conceito = contem_termos(
        [
            "explique",
            "explicar",
            "o que e",
            "o que é",
            "como funciona",
            "definicao",
            "definição",
        ]
    )

    extras: set[str] = set()
    if pede_exemplo and "exemplificador" not in base:
        extras.add("exemplificador")
    if (pede_diagnostico or pede_exercicio) and intencao.tipo not in {"selecao", "comparacao", "uso_incorreto"} and "inquiridor" not in base:
        extras.add("inquiridor")
    if pede_conceito and "tutor" not in base:
        extras.add("tutor")

    ativos = set(base) | extras
    ordenados = [nome for nome in ("tutor", "exemplificador", "inquiridor") if nome in ativos]
    return ordenados + ["guardiao"]
