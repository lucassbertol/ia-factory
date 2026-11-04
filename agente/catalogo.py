"""Catálogo de nomes de padrões conhecidos, usado pela barreira anti-alucinação.

Se o estudante pergunta por um "padrão X" e X não está aqui, o sistema não
deixa o modelo responder: um modelo de 3B tende a inventar uma explicação
plausível para qualquer nome. Os nomes estão normalizados (minúsculas, sem
acento) e cobrem português e inglês.
"""

from __future__ import annotations

# Nomes que se referem ao padrão ensinado ou a idiomas diretamente comparáveis.
FACTORY_METHOD = {
    "factory method", "factory", "metodo fabrica", "metodo de fabrica",
    "metodo-fabrica", "fabrica", "virtual constructor", "construtor virtual",
}

# Nomes que o sistema compara explicitamente com o Factory Method.
COMPARAVEIS = {
    "abstract factory", "fabrica abstrata", "simple factory", "fabrica simples",
    "static factory", "fabrica estatica", "static factory method",
    "template method", "metodo template", "metodo modelo", "metodo gabarito",
}

# Demais padrões GoF (existem, mas estão fora do escopo deste sistema).
OUTROS_GOF = {
    "builder", "construtor", "prototype", "prototipo", "singleton", "adapter",
    "adaptador", "bridge", "ponte", "composite", "composto", "decorator",
    "decorador", "facade", "fachada", "flyweight", "peso-mosca", "peso mosca",
    "proxy", "procurador", "chain of responsibility", "cadeia de responsabilidade",
    "cadeia de responsabilidades", "command", "comando", "interpreter",
    "interpretador", "iterator", "iterador", "mediator", "mediador", "memento",
    "lembranca", "observer", "observador", "state", "estado", "strategy",
    "estrategia", "visitor", "visitante",
}

# Padrões reais fora do GoF que estudantes costumam citar.
OUTROS_CONHECIDOS = {
    "mvc", "mvvm", "mvp", "dao", "repository", "repositorio", "service locator",
    "injecao de dependencia", "dependency injection", "object pool",
    "null object", "objeto nulo", "active record", "unit of work",
    "data mapper", "front controller", "publish subscribe", "pub sub",
}

# Palavras que podem vir logo depois de "padrão" sem ser um nome de padrão.
NAO_SAO_NOMES = {
    "de", "do", "da", "dos", "das", "e", "ou", "o", "a", "os", "as", "um", "uma",
    "que", "para", "pra", "no", "na", "em", "com", "se", "esse", "este", "isso",
    "projeto", "projetos", "criacional", "criacionais", "estrutural",
    "comportamental", "gof", "chamado", "chamada", "denominado", "conhecido",
    "como", "mais", "seria", "e", "eh", "voce", "certo", "correto", "ideal",
    "melhor", "aplicado", "usado", "ensinado", "acima", "anterior", "dele",
    "deles", "nesse", "neste", "ai", "aqui", "mesmo", "pelo", "pela", "ele",
    "ela", "sao", "foi", "tem", "por", "qual", "quais", "quando", "como",
    "seu", "sua", "meu", "minha", "nao", "sim",
}

TODOS = FACTORY_METHOD | COMPARAVEIS | OUTROS_GOF | OUTROS_CONHECIDOS

# Intenção de cada padrão GoF em uma frase (paráfrase do catálogo original).
# Usada para comparações e redirecionamentos, para que o modelo não precise
# "lembrar" a definição de outro padrão.
INTENCOES_GOF = {
    "Abstract Factory": "criacional; fornece uma interface para criar famílias de objetos relacionados sem especificar suas classes concretas",
    "Builder": "criacional; separa a construção de um objeto complexo da sua representação, para que o mesmo processo crie representações diferentes",
    "Factory Method": "criacional; define uma interface para criar um objeto, mas deixa as subclasses decidirem qual classe instanciar",
    "Prototype": "criacional; cria novos objetos copiando (clonando) uma instância protótipo",
    "Singleton": "criacional; garante que uma classe tenha uma única instância e um ponto global de acesso a ela",
    "Adapter": "estrutural; converte a interface de uma classe em outra interface que o cliente espera",
    "Bridge": "estrutural; desacopla uma abstração da sua implementação, para que as duas variem independentemente",
    "Composite": "estrutural; compõe objetos em árvores para tratar objetos individuais e composições de maneira uniforme",
    "Decorator": "estrutural; acrescenta responsabilidades a um objeto dinamicamente, como alternativa flexível às subclasses",
    "Facade": "estrutural; oferece uma interface única e simplificada para um conjunto de interfaces de um subsistema",
    "Flyweight": "estrutural; usa compartilhamento para suportar eficientemente grandes quantidades de objetos pequenos",
    "Proxy": "estrutural; fornece um substituto de outro objeto para controlar o acesso a ele",
    "Chain of Responsibility": "comportamental; passa uma requisição ao longo de uma cadeia de objetos até que um deles a trate",
    "Command": "comportamental; encapsula uma requisição como um objeto, permitindo parametrizar, enfileirar e desfazer operações",
    "Interpreter": "comportamental; define uma representação para a gramática de uma linguagem e um interpretador para ela",
    "Iterator": "comportamental; fornece acesso sequencial aos elementos de uma coleção sem expor sua representação",
    "Mediator": "comportamental; encapsula a forma como um conjunto de objetos interage, reduzindo o acoplamento entre eles",
    "Memento": "comportamental; captura e externaliza o estado interno de um objeto para restaurá-lo depois, sem violar o encapsulamento",
    "Observer": "comportamental; define uma dependência um-para-muitos para que, quando um objeto muda de estado, seus dependentes sejam notificados",
    "State": "comportamental; permite que um objeto (o Context) altere seu comportamento quando seu estado interno muda, delegando a um objeto State que é trocado por composição, e não por sobrescrita em subclasses",
    "Strategy": "comportamental; define uma família de algoritmos intercambiáveis e encapsulados; o objeto Context recebe uma Strategy por composição e pode trocá-la em tempo de execução, sem sobrescrita em subclasses do Context",
    "Template Method": "comportamental; define o esqueleto de um algoritmo em uma operação, deixando alguns passos para as subclasses",
    "Visitor": "comportamental; representa uma operação a ser executada sobre os elementos de uma estrutura de objetos sem mudar suas classes",
}

_APELIDOS = {
    "fabrica abstrata": "Abstract Factory", "construtor": "Builder", "prototipo": "Prototype",
    "metodo fabrica": "Factory Method", "metodo de fabrica": "Factory Method",
    "adaptador": "Adapter", "ponte": "Bridge", "composto": "Composite",
    "decorador": "Decorator", "fachada": "Facade", "peso-mosca": "Flyweight",
    "peso mosca": "Flyweight", "procurador": "Proxy",
    "cadeia de responsabilidade": "Chain of Responsibility",
    "cadeia de responsabilidades": "Chain of Responsibility", "comando": "Command",
    "interpretador": "Interpreter", "iterador": "Iterator", "mediador": "Mediator",
    "lembranca": "Memento", "observador": "Observer", "estado": "State",
    "estrategia": "Strategy", "metodo template": "Template Method",
    "metodo modelo": "Template Method", "metodo gabarito": "Template Method",
    "visitante": "Visitor",
}


def nome_canonico_gof(nome: str) -> str | None:
    """Nome GoF oficial a partir de um nome normalizado (ou None)."""
    nome = " ".join(nome.split())
    for oficial in INTENCOES_GOF:
        if nome == oficial.lower():
            return oficial
    return _APELIDOS.get(nome)


def padroes_gof_citados(texto_normalizado: str) -> list[str]:
    """Padrões GoF (exceto Factory Method) citados em um texto normalizado."""
    import re

    citados: list[str] = []
    candidatos = {oficial.lower(): oficial for oficial in INTENCOES_GOF}
    candidatos.update({k: v for k, v in _APELIDOS.items() if len(k) > 6})
    for termo, oficial in candidatos.items():
        if oficial == "Factory Method" or oficial in citados:
            continue
        if re.search(rf"\b{re.escape(termo)}\b", texto_normalizado):
            citados.append(oficial)
    return citados


def classificar_nome(nome: str) -> str:
    """Devolve 'factory_method', 'comparavel', 'outro' ou 'desconhecido'."""
    nome = " ".join(nome.split())
    if not nome:
        return "factory_method"
    if nome in FACTORY_METHOD:
        return "factory_method"
    if nome in COMPARAVEIS:
        return "comparavel"
    if nome in OUTROS_GOF or nome in OUTROS_CONHECIDOS:
        return "outro"
    # Nomes compostos que começam por um nome conhecido ("factory method em java").
    for conhecido in sorted(TODOS, key=len, reverse=True):
        if nome == conhecido or nome.startswith(conhecido + " "):
            return classificar_nome(conhecido)
    return "desconhecido"
