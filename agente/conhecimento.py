"""Conhecimento local verificado: referência, exemplos Java e diagrama.

Nada aqui acessa a rede. Os exemplos Java foram compilados e executados pela
dupla (ver tests/test_unitarios.py, que compila cada um quando há JDK).
O sistema exibe esses arquivos ao estudante em vez de pedir ao modelo de 3B
que escreva código do zero, porque nos testes o código gerado pelo modelo
não compilava ou misturava padrões.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import REFERENCIAS_DIR


@dataclass(frozen=True)
class ExemploJava:
    arquivo: str
    titulo: str
    saida_esperada: str

    @property
    def codigo(self) -> str:
        return (REFERENCIAS_DIR / self.arquivo).read_text(encoding="utf-8").strip()

    def bloco_markdown(self) -> str:
        return (
            f"**{self.titulo}** (arquivo `{self.arquivo}`, compilado e executado pela dupla)\n\n"
            f"```java\n{self.codigo}\n```\n\n"
            f"Saída ao executar `java {self.arquivo[:-5]}`:\n\n```\n{self.saida_esperada}\n```"
        )


EXEMPLOS = {
    "basico": ExemploJava(
        "ExemploFactoryMethod.java",
        "Exemplo verificado: notificações (Creator abstrato)",
        "Email para Ana\nSMS para Bia",
    ),
    "padrao": ExemploJava(
        "ExemploFactoryMethodPadrao.java",
        "Exemplo verificado: relatórios (Creator concreto com implementação padrão)",
        "[TXT] Relatorio de vendas\n[CSV] Relatorio;de;vendas",
    ),
    "incorreto": ExemploJava(
        "ExemploUsoIncorreto.java",
        "Exemplo de uso INCORRETO (compila, mas o padrão não funciona)",
        "Email para Bia",
    ),
    "simple_factory": ExemploJava(
        "ExemploSimpleFactory.java",
        "Contraste: Simple Factory (não é o Factory Method do GoF)",
        "Email simulado\nSMS simulado",
    ),
}

CORRECAO_USO_INCORRETO = """\
**Correção** (uma linha muda em `avisar()`):

```java
public String avisar(String destinatario) {
    Notificacao notificacao = criarNotificacao(); // usa o factory method
    return notificacao.enviar(destinatario);
}
```

Com essa mudança, `new NotificadorSms().avisar("Bia")` passa a imprimir `SMS para Bia`."""


def carregar_referencia() -> str:
    """Síntese conceitual que fundamenta as instruções de todos os agentes."""
    conteudo = (REFERENCIAS_DIR / "factory_method.md").read_text(encoding="utf-8")
    if not conteudo.strip():
        raise ValueError("Referência conceitual local vazia: factory_method.md")
    return conteudo


def carregar_uml() -> str:
    return (REFERENCIAS_DIR / "estrutura_uml.txt").read_text(encoding="utf-8").rstrip()


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


# ---------------------------------------------------------------- fatos dos exemplos
# Entregues ao Exemplificador junto com o código. Na quarta coleta (04/11) o
# modelo trocou papéis ("Email e Sms implementam a criação") e localizou mal o
# erro do exemplo incorreto; estes fatos verificados fixam essas respostas.
FATOS_EXEMPLOS = {
    "basico": (
        "Fatos verificados deste código: Notificacao é o Product; Email e Sms são os "
        "ConcreteProducts (não criam nada); Notificador é o Creator e declara o factory "
        "method criarNotificacao(); NotificadorEmail e NotificadorSms são os ConcreteCreators "
        "e sobrescrevem criarNotificacao(); avisar() é a operação de negócio e não muda. Para "
        "adicionar um produto novo (por exemplo, WhatsApp), cria-se uma classe Whatsapp que "
        "implementa Notificacao e uma classe NotificadorWhatsapp que estende Notificador; "
        "nenhuma classe existente é alterada, só o main passa a usar o novo criador."
    ),
    "padrao": (
        "Fatos verificados deste código: Exportador é o Product; ExportadorTexto e "
        "ExportadorCsv são os ConcreteProducts; Relatorio é o Creator e é uma classe "
        "concreta, com implementação padrão de criarExportador() (devolve texto); "
        "RelatorioCsv é o ConcreteCreator e sobrescreve criarExportador(); gerar() é a "
        "operação de negócio e não muda. Isso mostra que o Creator não precisa ser abstrato."
    ),
    "incorreto": (
        "Fatos verificados deste código: o erro está no método avisar() da classe "
        "Notificador (o Creator), que faz new Email() em vez de chamar criarNotificacao(). "
        "A subclasse NotificadorSms está correta, e o main também. Por isso a saída é "
        "'Email para Bia' em vez de 'SMS para Bia'. A correção muda uma linha em avisar(). "
        "Outros usos incorretos comuns: chamar de Factory Method um método static com "
        "if/switch (isso é Simple Factory) e criar a hierarquia sem variação real."
    ),
}


# ---------------------------------------------------------------- exercícios
@dataclass(frozen=True)
class Exercicio:
    ident: str
    enunciado: str
    gabarito: str  # nunca é mostrado ao estudante; serve para o Inquiridor avaliar


EXERCICIOS = [
    Exercicio(
        "recibos",
        "**Exercício: recibos**\n\n"
        "Uma loja emite recibos em PDF e em texto. O método `emitir()` faz sempre os mesmos "
        "passos (registra a venda e entrega o recibo); só muda o tipo de recibo criado. A loja "
        "quer, no futuro, emitir recibos em HTML sem mexer em `emitir()`.\n\n"
        "Usando o Factory Method, quais classes seriam o Product, os ConcreteProducts, o "
        "Creator e os ConcreteCreators? Não precisa escrever código: descreva as classes e "
        "quem sobrescreve o quê.\n\n"
        "Para começar: quem seria o Product?",
        "Product: Recibo (interface). ConcreteProducts: ReciboPdf e ReciboTexto. Creator: "
        "Emissor, com emitir() (operação de negócio) e criarRecibo() (factory method). "
        "ConcreteCreators: EmissorPdf e EmissorTexto, que sobrescrevem criarRecibo(). emitir() "
        "chama criarRecibo() e usa o Recibo só pela interface. Para HTML: criar ReciboHtml e "
        "EmissorHtml, sem alterar emitir(). Erros comuns: colocar if/switch dentro de "
        "emitir(); dizer que ReciboPdf sobrescreve o factory method; usar um método static.",
    ),
    Exercicio(
        "simple_factory",
        "**Exercício: é Factory Method?**\n\n"
        "Uma colega escreveu o código abaixo para criar formas de pagamento e disse que "
        "aplicou o padrão Factory Method:\n\n"
        "```java\nclass FabricaPagamento {\n    static Pagamento criar(String tipo) {\n"
        "        if (tipo.equals(\"pix\")) return new Pix();\n        return new Cartao();\n"
        "    }\n}\n```\n\n"
        "Ela está certa? Explique o porquê e descreva, sem escrever o código completo, como "
        "transformar isso em Factory Method.\n\n"
        "Para começar: neste código, existe alguma subclasse sobrescrevendo um método de criação?",
        "Não é Factory Method: é Simple Factory (método static com if, escolha centralizada, "
        "sem sobrescrita em subclasses; não é padrão GoF). Para virar Factory Method: um "
        "Creator (por exemplo, Caixa) com a operação de negócio finalizarCompra() que chama o "
        "factory method criarPagamento() (método de instância, não static); ConcreteCreators "
        "CaixaPix e CaixaCartao sobrescrevem criarPagamento() devolvendo new Pix() e new "
        "Cartao(); Pagamento é o Product. Uma forma nova de pagamento exige novas classes, "
        "sem editar finalizarCompra(). Simple Factory não é errado em si; só não é o padrão.",
    ),
    Exercicio(
        "extensao",
        "**Exercício: estender o exemplo**\n\n"
        "No exemplo verificado das notificações (`Notificacao`, `Email`, `Sms`, `Notificador`, "
        "`NotificadorEmail` e `NotificadorSms`), a empresa quer enviar avisos também por "
        "WhatsApp.\n\n"
        "Quais classes você criaria e quais classes existentes precisariam mudar? Lembre que "
        "`avisar()` não deve ser alterado.\n\n"
        "Para começar: qual classe nova representa o produto WhatsApp e o que ela implementa?",
        "Criar Whatsapp implements Notificacao (ConcreteProduct) e NotificadorWhatsapp extends "
        "Notificador, sobrescrevendo criarNotificacao() para devolver new Whatsapp() "
        "(ConcreteCreator). Nenhuma classe existente muda (nem Notificador, nem avisar(), nem "
        "NotificadorEmail/NotificadorSms, nem a interface); só o código de configuração (main) "
        "passa a instanciar NotificadorWhatsapp. Erros comuns: pôr um if em avisar(); alterar "
        "NotificadorSms; mudar a interface Notificacao.",
    ),
]


def escolher_exercicio(ja_propostos: list[str]) -> Exercicio:
    """Próximo exercício ainda não proposto na sessão (volta ao início depois)."""
    for exercicio in EXERCICIOS:
        if exercicio.ident not in ja_propostos:
            return exercicio
    ultimo = ja_propostos[-1] if ja_propostos else ""
    return next((e for e in EXERCICIOS if e.ident != ultimo), EXERCICIOS[0])


def exercicio_por_id(ident: str) -> Exercicio | None:
    return next((e for e in EXERCICIOS if e.ident == ident), None)
