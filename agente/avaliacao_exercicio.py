"""Avaliação determinística das tentativas do exercício de recibos.

Por que existe: no teste da interface web (04/11), o Inquiridor de 3B copiou o
começo do gabarito para o estudante e, diante de uma tentativa toda correta
(Product, ConcreteProducts, Creator e ConcreteCreators), inventou equívocos.
Comparar uma resposta livre com o gabarito não é confiável num modelo pequeno.

Aqui o sistema confere a tentativa parte por parte, sem modelo. O resultado vai
para o Inquiridor como fato verificado (ele só redige o retorno), define a
pergunta seguinte e serve de resposta segura quando o texto do modelo não passa
na validação. O gabarito deixa de ser enviado ao modelo neste exercício.

Como funciona: cada oração da tentativa é ligada ao papel que cita (Product,
ConcreteProduct, Creator, ConcreteCreator). Os nomes ligados a um papel são
classificados pelo tipo ("emissor"/"gerador" = quem cria; "recibo" = o que é
criado) e pela variante (pdf, texto, html). Nomes diferentes dos do gabarito
valem se o papel estiver certo ("EmissorRecibo" serve como Creator).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .fluxo_heuristico import normalizar_pergunta

PAPEIS = ("Product", "ConcreteProducts", "Creator", "ConcreteCreators")

# Ordem importa: os papéis concretos são procurados (e mascarados) antes.
_PAPEL_EXPR = (
    ("ConcreteProducts", r"\bconcret\w*\s?products?\b|\bprodutos?\s+concretos?\b"),
    ("ConcreteCreators", r"\bconcret\w*\s?creators?\b|\bcriador(?:es)?\s+concretos?\b"),
    ("Product", r"\bproducts?\b|\bprodutos?\b"),
    ("Creator", r"\bcreators?\b|\bcriador(?:es)?\b"),
)
# "é" vira "eh" antes de tirar os acentos, para não confundir com a conjunção "e".
_VERBO = r"(?:seria|seriam|sera|serao|eh|sao|fica|ficaria|ficariam)"
_QUEM_CRIA = re.compile(r"emissor|emitente|gerador|criador\s*de\s*recibo|fabrica\s*de\s*recibo")
_O_QUE_E_CRIADO = re.compile(r"recibo")
_VARIANTE = {"pdf": r"pdf", "texto": r"texto|txt", "html": r"html"}

_ARTIGO = {"Product": "o", "ConcreteProducts": "os", "Creator": "o", "ConcreteCreators": "os"}

_PERGUNTA_PARTE = {
    "Product": "Quem seria o Product, o contrato comum a todos os recibos?",
    "ConcreteProducts": "Quais seriam os ConcreteProducts, os tipos concretos de recibo?",
    "Creator": "Qual classe seria o Creator, a que tem emitir() e declara o método que cria o recibo?",
    "ConcreteCreators": "Quais classes seriam os ConcreteCreators e o que elas sobrescrevem?",
}


@dataclass
class Parte:
    papel: str  # nome da parte do exercício
    certo: bool
    citado: str  # o que o estudante escreveu para essa parte
    ajuste: str = ""
    termos: tuple[str, ...] = ()  # o texto do Inquiridor precisa citar um deles ao explicar o ajuste
    elogio: str = ""  # frase do retorno verificado quando a parte está certa


@dataclass
class AvaliacaoTentativa:
    partes: dict[str, Parte] = field(default_factory=dict)
    erros: list[str] = field(default_factory=list)
    html: str = ""  # "", "certo" ou o ajuste necessário (só no exercício de recibos)
    pergunta: str = ""
    ordem: tuple[str, ...] = PAPEIS  # partes do exercício, na ordem em que são pedidas
    exige_html: bool = True
    conclusao: str = ""  # retorno quando tudo está certo (exercícios sem HTML)

    @property
    def faltam(self) -> list[str]:
        return [p for p in self.ordem if p not in self.partes]

    @property
    def erradas(self) -> list[Parte]:
        return [p for p in self.partes.values() if not p.certo]

    @property
    def sem_equivocos(self) -> bool:
        return not self.erradas and not self.erros and self.html in ("", "certo")

    @property
    def concluido(self) -> bool:
        return self.sem_equivocos and not self.faltam and (self.html == "certo" or not self.exige_html)

    def fatos(self) -> str:
        """Resultado para o Inquiridor e o Guardião (sem nomes do gabarito)."""
        linhas = ["Avaliação verificada pelo sistema (não reavalie e não contradiga):"]
        for papel in self.ordem:
            parte = self.partes.get(papel)
            if parte is None:
                linhas.append(f"- {papel}: ainda não respondido.")
            elif parte.certo:
                linhas.append(f"- {papel}: CORRETO.")
            else:
                linhas.append(f"- {papel}: PRECISA DE AJUSTE. Motivo: {parte.ajuste}")
        linhas += [f"- Equívoco na tentativa: {e}" for e in self.erros]
        if self.html == "certo":
            linhas.append("- Extensão para HTML: CORRETA.")
        elif self.html:
            linhas.append(f"- Extensão para HTML: PRECISA DE AJUSTE. Motivo: {self.html}")
        if self.sem_equivocos:
            linhas.append("Não há nenhum equívoco: não aponte erros.")
        return "\n".join(linhas)

    def texto(self) -> str:
        """Retorno determinístico ao estudante (sem a pergunta final)."""
        if not self.exige_html:
            if self.concluido:
                return self.conclusao
            frases = [p.elogio for p in self.partes.values() if p.certo and p.elogio]
            frases += [p.ajuste for p in self.erradas] + self.erros
            return " ".join(frases) or "Vamos por partes."
        certas = [p.papel for p in self.partes.values() if p.certo]
        frases = []
        if self.concluido:
            frases.append("Excelente: você identificou corretamente os quatro participantes e "
                          "estendeu a solução para HTML sem mexer em emitir(). Exercício concluído!")
        elif len(certas) == len(PAPEIS):
            frases.append("Muito bem: o Product, os ConcreteProducts, o Creator e os "
                          "ConcreteCreators estão corretos.")
        elif certas:
            frases.append("Certo: " + _lista([f"{_ARTIGO[p]} {p}" for p in certas]) + ".")
        for parte in self.erradas:
            frases.append(f"Sobre {_ARTIGO[parte.papel]} {parte.papel}: {parte.ajuste}")
        frases += self.erros
        if self.html and self.html != "certo":
            frases.append(self.html)
        if self.html == "certo" and not self.concluido:
            frases.append("A extensão para HTML está certa.")
        return " ".join(frases) or "Vamos por partes."


def _lista(itens: list[str]) -> str:
    return itens[0] if len(itens) == 1 else ", ".join(itens[:-1]) + " e " + itens[-1]


def _tipo(trecho: str) -> tuple[str, set[str]]:
    """("cria" | "criado" | "", variantes) do que foi escrito num trecho."""
    trecho = re.sub(r"\([^)]*\)", " ", trecho)  # explicações entre parênteses
    variantes = {v for v, e in _VARIANTE.items() if re.search(e, trecho)}
    if _QUEM_CRIA.search(trecho):
        return "cria", variantes
    if _O_QUE_E_CRIADO.search(trecho):
        return "criado", variantes
    return "", variantes


def _julgar(papel: str, trecho: str) -> Parte | None:
    tipo, variantes = _tipo(trecho)
    citado = " ".join(re.sub(r"\([^)]*\)", " ", trecho).split()).strip(" :,-–") or trecho.strip()
    citado = re.sub(r"\beh\b", "é", citado)
    if not tipo:
        return None
    concreto = papel.startswith("Concrete")
    base_certa = "criado" if papel.endswith("Products") or papel == "Product" else "cria"
    if tipo != base_certa:
        ajuste = {
            "criado": "um recibo é o que é criado; quem cria é a classe que tem emitir() "
                      "e o método de criação (e as subclasses dela).",
            "cria": "essa classe é a que cria os recibos; o Product e os ConcreteProducts "
                    "são os próprios recibos.",
        }[tipo]
        return Parte(papel, False, citado, ajuste)
    if concreto and not variantes:
        return Parte(papel, False, citado,
                     "os concretos são as versões específicas, uma para PDF e outra para texto.")
    if not concreto and variantes:
        return Parte(papel, False, citado,
                     "uma classe específica de PDF ou de texto é concreta; o "
                     f"{papel} é o tipo geral, comum a todas as versões.")
    return Parte(papel, True, citado)


def _oracoes(texto: str) -> list[str]:
    papel = r"(?:concret\w*\s?)?(?:products?|produtos?|creators?|criador\w*)\b"
    return [o for o in re.split(
        rf"[.;\n]+|,\s*(?=(?:e\s+)?(?:o|a|os|as)\s)|\s+e\s+(?=(?:o|a|os|as)\s+{papel})", texto)
        if o.strip()]


def _ligar_papeis(oracao: str) -> list[tuple[str, str]]:
    """[(papel, trecho com os nomes)] de uma oração."""
    mascarada = oracao
    mencoes = []
    for papel, expressao in _PAPEL_EXPR:
        for m in re.finditer(expressao, mascarada):
            mencoes.append((m.start(), m.end(), papel))
        mascarada = re.sub(expressao, lambda m: "#" * len(m.group(0)), mascarada)
    mencoes.sort()
    ligacoes = []
    fim_verbo = rf"\b{_VERBO}\s+(?:o|a|os|as)?\s*$"
    for i, (ini, fim, papel) in enumerate(mencoes):
        anterior_fim = mencoes[i - 1][1] if i else 0
        proximo_ini = mencoes[i + 1][0] if i + 1 < len(mencoes) else len(oracao)
        depois = oracao[fim:proximo_ini]
        antes = oracao[anterior_fim:ini]
        # "o product seria o recibo ReciboPdf e ReciboTexto são os ConcreteProducts":
        # o sujeito de "são os ConcreteProducts" não pertence ao Product.
        sujeito = re.search(rf"(\w+(?:\s*(?:,|\be\b)\s*\w+)*)\s+{_VERBO}\s+(?:o|a|os|as)?\s*$", depois)
        if sujeito and i + 1 < len(mencoes):
            depois = depois[: sujeito.start(1)]
        if re.search(fim_verbo, antes):  # "Recibo é o Product"
            trecho = antes
        elif re.match(rf"\s*(?:[:=\-–]|{_VERBO}\b)", depois):  # "Product: Recibo"
            trecho = depois
        else:
            trecho = depois if _tipo(depois)[0] else antes
        ligacoes.append((papel, trecho))
    return ligacoes


def avaliar_recibos(fala: str) -> AvaliacaoTentativa:
    """Avalia tudo o que o estudante escreveu no exercício (a última menção vale)."""
    texto = _normalizar(fala)
    av = AvaliacaoTentativa()
    for oracao in _oracoes(texto):
        for papel, trecho in _ligar_papeis(oracao):
            parte = _julgar(papel, trecho)
            if parte:
                av.partes[papel] = parte
    if re.search(r"\b(?:if|switch|else)\b", texto) and not re.search(r"\b(?:sem|nao|nenhum)\b[^.]{0,30}\b(?:if|switch)", texto):
        av.erros.append("Um if/switch para escolher o tipo de recibo é justamente o que o "
                        "Factory Method evita: cada subclasse decide o recibo ao sobrescrever "
                        "o método de criação.")
    if re.search(r"\bstatic\b|\bestatic[oa]\b", texto):
        av.erros.append("O método de criação não pode ser static: ele precisa ser sobrescrito "
                        "pelas subclasses.")
    if re.search(r"\brecibo\s?(?:pdf|texto|txt|html)\w*\s+(?:que\s+)?(?:sobrescrev|redefin)", texto):
        av.erros.append("Quem sobrescreve o método de criação são as subclasses de quem cria "
                        "(os ConcreteCreators), não os recibos concretos.")
    if "html" in texto:
        cria = re.search(r"(?:emissor|gerador)\w*\s?html", texto)
        criado = re.search(r"recibo\s?html", texto)
        altera = re.search(r"(?<!sem )(?<!nao )\b(?:alter|mud|modific|mex)\w*\s+(?:no |o |em )?emitir", texto)
        if cria and criado and not altera:
            av.html = "certo"
        elif altera:
            av.html = "Para HTML, emitir() não deve mudar: basta acrescentar classes novas."
        else:
            av.html = ("Para HTML faltam as duas classes novas: o recibo em HTML e a subclasse "
                       "que o cria.")
    av.pergunta = _proxima_pergunta(av)
    return av


def _proxima_pergunta(av: AvaliacaoTentativa) -> str:
    if av.concluido:
        return "Quer tentar outro exercício ou revisar algum ponto do Factory Method?"
    if av.erradas:
        papel = av.erradas[0].papel
        return f"Como você ajustaria {_ARTIGO[papel]} {papel}?"
    if av.erros:
        return "Como você ajustaria isso na sua solução?"
    if av.faltam:
        return _PERGUNTA_PARTE[av.faltam[0]]
    if av.html and av.html != "certo":
        return "Como ficaria a extensão para HTML?"
    return "Agora, o que você criaria para emitir recibos em HTML sem mexer em emitir()?"


def _normalizar(fala: str) -> str:
    """Normaliza linha a linha: cada mensagem do estudante fica na sua linha (antes,
    as mensagens viravam uma linha só e os nomes de uma passavam para a outra)."""
    linhas = []
    for linha in fala.splitlines():
        linha = re.sub(r"(?i)(?<!\w)é(?!\w)", "eh", linha)
        linhas.append(re.sub(r"\bminha (?:resposta|tentativa)\s*:?", " ", normalizar_pergunta(linha)))
    return "\n".join(linhas)


def _frases(fala: str) -> list[str]:
    texto = _normalizar(fala)
    return [f.strip() for f in re.split(r"(?<=[.!?;])\s+|\n+", texto) if f.strip()]


_NEGA = r"\b(?:nao|nenhum\w*|sem|nunca)\b"


# ------------------------------------------------------------ simple_factory
# Enunciado: "Ela está certa? Explique o porquê e descreva como transformar isso
# em Factory Method. Para começar: existe alguma subclasse sobrescrevendo um
# método de criação?" Teste web de 04/11: à resposta correta "Não, não existe
# nenhuma subclasse sobrescrevendo...", o modelo respondeu "Não está correto".
SF_PARTES = ("Sobrescrita", "Veredito", "Transformação")


def avaliar_simple_factory(fala: str) -> AvaliacaoTentativa:
    av = AvaliacaoTentativa(ordem=SF_PARTES, exige_html=False, conclusao=(
        "Excelente: você viu que não há subclasse sobrescrevendo o método de criação, que o "
        "código é uma Simple Factory (não é errado, só não é o padrão) e descreveu a "
        "transformação em Factory Method. Exercício concluído!"))
    for frase in _frases(fala):
        # "Sim"/"Não" sozinhos respondem à pergunta guia em aberto.
        resposta_curta = re.fullmatch(
            r"(?:sim|nao)(?:,?\s*(?:existe|tem|ha|nao existe|nao tem|nao ha|nenhuma)(?:\s+sim)?)?[.!]?"
            r"|(?:nao (?:existe|tem|ha)|nenhuma|existe(?: sim)?|tem(?: sim)?)[.!]?", frase)
        if resposta_curta and "Sobrescrita" not in av.partes:
            certo = bool(re.match(r"nao|nenhuma", frase))
            av.partes["Sobrescrita"] = Parte("Sobrescrita", certo, frase, termos=("subclasse", "sobrescrev"),
                elogio="Certo: não há nenhuma subclasse redefinindo o método de criação; "
                       "FabricaPagamento é uma classe só." if certo else "",
                ajuste="" if certo else "Neste código não há subclasse: FabricaPagamento é uma "
                       "classe só, com um método static que escolhe o tipo com if.")
            continue
        if re.fullmatch(r"sim[.!]?", frase) and "Veredito" not in av.partes:
            av.partes["Veredito"] = Parte("Veredito", False, frase, termos=("Simple Factory", "Factory Method"),
                ajuste="Ela não aplicou o Factory Method: sem subclasses sobrescrevendo um método de "
                       "criação, um método static com if é uma Simple Factory.")
            continue
        subclasse = re.search(r"\bsub ?class\w*|\bheran\w*|\bherd\w*|\bsobrescr\w*|\bredefin\w*", frase)
        # 1. Existe subclasse sobrescrevendo um método de criação? (resposta certa: não)
        if subclasse and re.search(rf"{_NEGA}[^.?!]{{0,40}}(?:sub ?class|heran|herd|sobrescr|redefin)", frase) \
                and not re.search(r"\bnao sei\b", frase) and not re.search(r"\b(?:criaria|faria|teria que|precisa)\b", frase):
            av.partes["Sobrescrita"] = Parte("Sobrescrita", True, frase, termos=("subclasse", "sobrescrev"),
                elogio="Certo: não há nenhuma subclasse redefinindo o método de criação; "
                       "FabricaPagamento é uma classe só.")
        elif re.match(r"\s*sim\b", frase) or re.search(rf"(?<!nao )\b(?:existe|tem|ha)\s+(?:uma\s+)?sub ?class", frase):
            av.partes["Sobrescrita"] = Parte("Sobrescrita", False, frase, termos=("subclasse", "sobrescrev"),
                ajuste="Neste código não há subclasse: FabricaPagamento é uma classe só, com um "
                       "método static que escolhe o tipo com if.")
        # 2. Ela está certa? (resposta certa: não, é Simple Factory)
        nega_fm = re.search(r"\bnao\s+(?:eh|e|esta|seria|foi|se trata de|usa|aplicou)\b[^.?!]{0,30}\bfactory method\b"
                            r"|\bnao\s+(?:esta\s+certa|aplicou)\b|\besta\s+errada\b|\bse\s+enganou\b"
                            r"|(?<!nao eh )(?<!nao e )\bsimple factory\b", frase)
        afirma_fm = re.search(r"(?<!nao )\b(?:esta\s+certa|aplicou\s+(?:o\s+)?(?:padrao\s+)?factory method)\b"
                              r"|^\s*sim\b[^.?!]*factory method|\bnao\s+eh\s+(?:uma\s+)?simple factory", frase)
        if not nega_fm and "Sobrescrita" in av.partes and re.fullmatch(
                r"(?:nao|nao,? (?:ela )?nao esta(?: certa)?|ela nao esta certa|nao esta)[.!]?", frase):
            nega_fm = True  # "Não." em resposta a "Então, ela está certa?"
        if nega_fm:
            av.partes["Veredito"] = Parte("Veredito", True, frase, termos=("Simple Factory", "Factory Method"),
                elogio="Exato: ela não aplicou o Factory Method; isso é uma Simple Factory, "
                       "que não é errada, só não é o padrão GoF.")
        elif afirma_fm:
            av.partes["Veredito"] = Parte("Veredito", False, frase, termos=("Simple Factory", "Factory Method"),
                ajuste="Ela não aplicou o Factory Method: sem subclasses sobrescrevendo um método de "
                       "criação, um método static com if é uma Simple Factory.")
        # 3. Como transformar em Factory Method
        if subclasse and re.search(r"\b(?:criar|criaria|crie|faria|teria|usar|usaria|transform\w*|precisaria|"
                                   r"deveria|cada subclasse|subclasses? (?:que|para|como)|com subclasses)\b", frase) \
                and not re.search(rf"{_NEGA}[^.?!]{{0,15}}(?:sub ?class|sobrescr)", frase):
            if re.search(rf"(?<!sem )(?<!tirar o )(?<!tirar )(?<!remover o )(?<!nao )\b(?:manter|mantem|manteria|continua\w*)\b[^.?!]{{0,20}}static", frase):
                av.partes["Transformação"] = Parte("Transformação", False, frase, termos=("static",),
                    ajuste="O método de criação não pode continuar static: um método static não é "
                           "sobrescrito pelas subclasses.")
            elif re.search(r"(?<!sem )(?<!tirar o )\b(?:if|switch)\b", frase) and not re.search(rf"{_NEGA}[^.?!]{{0,20}}\b(?:if|switch)\b|\b(?:tirar|remover|eliminar)\w*[^.?!]{{0,10}}\b(?:if|switch)\b", frase):
                av.partes["Transformação"] = Parte("Transformação", False, frase, termos=("if",),
                    ajuste="No Factory Method o if desaparece: cada subclasse cria um único tipo de pagamento.")
            elif re.search(r"\bsobrescr\w*|\bredefin\w*|\boverride\b|\bimplement\w*", frase):
                av.partes["Transformação"] = Parte("Transformação", True, frase, termos=("subclasse",),
                    elogio="Isso transforma o código em Factory Method: o método de criação deixa de ser "
                           "static e cada subclasse decide a forma de pagamento ao sobrescrevê-lo.")
            elif "Transformação" not in av.partes:
                av.partes["Transformação"] = Parte("Transformação", False, frase, termos=("sobrescrev",),
                    ajuste="Falta dizer o que as subclasses fazem: cada uma sobrescreve o método de "
                           "criação e devolve um tipo de pagamento.")
    if "Sobrescrita" not in av.partes and av.partes.get("Veredito", Parte("", False, "")).certo:
        av.partes["Sobrescrita"] = Parte("Sobrescrita", True, "", elogio="")
    falta = av.faltam
    if av.concluido:
        av.pergunta = "Quer tentar outro exercício ou revisar algum ponto do Factory Method?"
    elif av.erradas:
        av.pergunta = {
            "Sobrescrita": "Olhe de novo: alguma classe neste código herda de outra e redefine criar()?",
            "Veredito": "Sem subclasses sobrescrevendo um método de criação, isso pode ser Factory "
                        "Method? Como se chama um método static que escolhe o tipo com if?",
            "Transformação": "Como você ajustaria a transformação?",
        }[av.erradas[0].papel]
    elif falta and falta[0] == "Sobrescrita":
        av.pergunta = "Neste código, existe alguma subclasse sobrescrevendo um método de criação?"
    elif falta and falta[0] == "Veredito":
        av.pergunta = ("Então, ela está certa ao dizer que aplicou o Factory Method? Que nome tem "
                       "essa forma de criar objetos?")
    else:
        av.pergunta = ("Como você transformaria isso em Factory Method: quem teria o método de "
                       "criação e quem o sobrescreveria?")
    return av


# ------------------------------------------------------------ extensao
# Enunciado: no exemplo das notificações, acrescentar WhatsApp. "Quais classes
# você criaria e quais classes existentes precisariam mudar? Lembre que avisar()
# não deve ser alterado."
EX_PARTES = ("Produto novo", "Criador novo", "O que muda")


def avaliar_extensao(fala: str) -> AvaliacaoTentativa:
    av = AvaliacaoTentativa(ordem=EX_PARTES, exige_html=False, conclusao=(
        "Excelente: um ConcreteProduct novo para WhatsApp, um ConcreteCreator novo que o cria, e "
        "nenhuma classe existente do padrão precisa mudar (só a configuração no main escolhe o "
        "criador novo). Exercício concluído!"))
    for frase in _frases(fala):
        criador = re.search(r"notificador\s?whats\w*|whats\w*\s?notificador|"
                            r"\b(?:estend|herd|extends|subclasse de notificador)\w*[^.?!]{0,25}\bnotificador\b|"
                            r"\bnotificador\b[^.?!]{0,10}\bwhats", frase)
        produto = re.search(r"(?<!notificador)(?<!notificador )\bwhats\w*", frase) and re.search(
            r"\bimplement\w*[^.?!]{0,25}\bnotificac\w*|\bnotificac\w*\b[^.?!]{0,25}\bimplement|"
            r"\bconcrete ?products?\b|\bprodutos? concretos?\b|\binterface\b", frase)
        # Produto: classe WhatsApp que implementa Notificacao
        if produto and not re.search(r"notificador\s?whats\w*[^.?!]{0,15}implement", frase):
            av.partes["Produto novo"] = Parte("Produto novo", True, frase, termos=("WhatsApp", "Whatsapp"),
                elogio="Certo: o produto novo é uma classe de WhatsApp que implementa Notificacao.")
        elif re.search(r"notificador\s?whats\w*[^.?!]{0,15}implement\w*[^.?!]{0,15}notificac", frase):
            av.partes["Produto novo"] = Parte("Produto novo", False, frase, termos=("WhatsApp", "Whatsapp"),
                ajuste="Quem implementa Notificacao é o produto (a classe de WhatsApp); o "
                       "NotificadorWhatsapp é o criador, que estende Notificador.")
        # Criador: NotificadorWhatsapp estende Notificador e sobrescreve criarNotificacao()
        if criador:
            if re.search(r"\bimplement\w*[^.?!]{0,10}\bnotificac", frase) and not produto:
                pass  # tratado acima
            else:
                av.partes["Criador novo"] = Parte("Criador novo", True, frase, termos=("Notificador",),
                    elogio="Certo: o criador novo estende Notificador e sobrescreve "
                           "criarNotificacao() para devolver o produto de WhatsApp.")
        # O que muda
        mudanca = re.search(r"\b(?:mud|alter|modific|mex)\w*", frase)
        if mudanca or re.search(r"\bnenhuma\b|\bso o main\b|\bapenas o main\b|\bsomente o main\b", frase):
            muda_errado = re.search(
                r"(?<!nao )(?<!sem )\b(?:mud|alter|modific|mex)\w*\s+(?:em |no |na |o |a )?"
                r"(?:avisar|notificacao|interface|notificadorsms|notificadoremail|notificador\b)", frase)
            nega = re.search(rf"{_NEGA}[^.?!]{{0,25}}\b(?:mud|alter|modific|mex)\w*", frase)
            if re.search(r"\bif\b[^.?!]{0,20}avisar|avisar[^.?!]{0,20}\bif\b", frase) and not re.search(rf"{_NEGA}[^.?!]{{0,15}}\bif\b", frase):
                av.erros.append("Um if em avisar() é o que o padrão evita: avisar() continua igual e "
                                "a escolha fica com o criador novo.")
            elif muda_errado and not nega:
                av.partes["O que muda"] = Parte("O que muda", False, frase, termos=("mud", "alter"),
                    ajuste="Nenhuma classe existente do padrão precisa mudar (Notificacao, "
                           "Notificador, NotificadorEmail e NotificadorSms ficam iguais); só o "
                           "main passa a usar o criador novo.")
            elif nega or re.search(r"\bnenhuma\b|\b(?:so|apenas|somente) o main\b|\bmain\b", frase):
                av.partes["O que muda"] = Parte("O que muda", True, frase, termos=("mud", "alter"),
                    elogio="Isso mesmo: as classes existentes não mudam; só a configuração no "
                           "main passa a escolher o criador novo.")
    if av.concluido:
        av.pergunta = "Quer tentar outro exercício ou revisar algum ponto do Factory Method?"
    elif av.erradas or av.erros:
        av.pergunta = "Como você ajustaria isso?"
    else:
        av.pergunta = {
            "Produto novo": "Qual classe nova representa o produto WhatsApp e o que ela implementa?",
            "Criador novo": "E qual classe nova cria esse produto? De quem ela herda e o que sobrescreve?",
            "O que muda": "Quais classes existentes precisariam mudar para isso funcionar?",
        }[av.faltam[0]]
    return av


AVALIADORES = {
    "recibos": avaliar_recibos,
    "simple_factory": avaliar_simple_factory,
    "extensao": avaliar_extensao,
}
