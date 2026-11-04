# Rubrica do caderno de evidências

Critérios usados pela dupla para julgar cada resposta dos sistemas avaliados nas
sessões de 13/11. O objetivo é que duas pessoas diferentes, lendo a mesma
resposta, cheguem à mesma nota. Por isso cada nível tem uma definição objetiva,
e toda nota deve vir com o trecho da resposta que a justifica.

## 1. Correção conceitual (0–2)

| Nota | Definição |
|---|---|
| 2 | Intenção, participantes e relações batem com o catálogo GoF (tabela da seção 5). Nenhuma afirmação falsa. |
| 1 | Simplificação ou imprecisão que não levaria o estudante a erro (ex.: omite um participante, termo vago). |
| 0 | Pelo menos um erro que ensinaria algo errado: papéis trocados, padrão confundido com outro, consequência inventada, fonte ou "fato" inventado. |

## 2. Utilidade pedagógica (0–2)

| Nota | Definição |
|---|---|
| 2 | Responde exatamente ao que foi pedido, em linguagem de iniciante, e deixa um próximo passo (pergunta, desafio). |
| 1 | Responde em parte, de forma genérica, longa demais ou em outra ordem do pedido. |
| 0 | Não responde ao pedido (ex.: pediu diferença e recebeu exercício; pediu exemplo e recebeu só teoria). |

## 3. Anti-alucinação (S / N / NA)

Aplica-se aos cenários 6a, 6b e aos extras E1–E3; nos demais, marque NA, a menos que a resposta invente algo (aí marque N).

- **S:** recusou com educação, explicou por quê e ofereceu um caminho (6a, E1); orientou em vez de entregar a solução (6b, E3); corrigiu a premissa falsa (E2).
- **N:** inventou o padrão ou participantes, entregou solução completa pronta, ou aceitou a premissa falsa.

## 4. Código Java (0–2 / NA)

Aplica-se quando a resposta traz código (cenários 2 e 4, principalmente).

| Nota | Definição |
|---|---|
| 2 | Compila (teste com `javac` copiando o código para um arquivo) e implementa de fato o padrão pedido. |
| 1 | Pequeno erro de compilação, ou compila mas a estrutura do padrão está incompleta. |
| 0 | Não compila de forma grave, está em outra linguagem, ou implementa outro padrão. |

## 5. Gabarito de apoio: padrões disponíveis no trabalho

Fonte: Gamma, Helm, Johnson e Vlissides, *Design Patterns* (1994). Use para
checar a correção conceitual das respostas dos outros sistemas.

| Padrão | Tipo | Intenção (resumo) | Participantes GoF | Confusões comuns |
|---|---|---|---|---|
| Factory Method | Criacional | Interface para criar um objeto; subclasses decidem a classe concreta | Product, ConcreteProduct, Creator, ConcreteCreator | Simple Factory, Abstract Factory |
| Abstract Factory | Criacional | Interface para criar famílias de objetos relacionados sem especificar classes concretas | AbstractFactory, ConcreteFactory, AbstractProduct, ConcreteProduct, Client | Factory Method |
| Builder | Criacional | Separa a construção de um objeto complexo da sua representação | Builder, ConcreteBuilder, Director, Product | Abstract Factory, construtor com muitos parâmetros |
| Prototype | Criacional | Cria objetos clonando uma instância protótipo | Prototype, ConcretePrototype, Client | Cópia rasa × profunda; Factory Method |
| Adapter | Estrutural | Converte a interface de uma classe na interface esperada pelo cliente | Target, Client, Adaptee, Adapter | Bridge, Decorator, Facade |
| Bridge | Estrutural | Desacopla abstração e implementação para variarem independentemente | Abstraction, RefinedAbstraction, Implementor, ConcreteImplementor | Adapter, Strategy |
| Composite | Estrutural | Compõe objetos em árvore e trata folhas e composições de forma uniforme | Component, Leaf, Composite, Client | Decorator |
| Flyweight | Estrutural | Compartilha objetos para suportar muitos objetos pequenos (estado intrínseco × extrínseco) | Flyweight, ConcreteFlyweight, UnsharedConcreteFlyweight, FlyweightFactory, Client | Singleton, pool de objetos |
| Proxy | Estrutural | Substituto que controla o acesso a outro objeto | Subject, RealSubject, Proxy | Decorator, Adapter |
| Command | Comportamental | Encapsula uma requisição como objeto (filas, log, desfazer) | Command, ConcreteCommand, Client, Invoker, Receiver | Strategy |
| Iterator | Comportamental | Acesso sequencial aos elementos de uma coleção sem expor sua estrutura | Iterator, ConcreteIterator, Aggregate, ConcreteAggregate | Visitor, laço for-each |
| Memento | Comportamental | Captura e restaura o estado interno de um objeto sem violar o encapsulamento | Memento, Originator, Caretaker | Command (desfazer), Prototype |
| Observer | Comportamental | Dependência um-para-muitos: dependentes são notificados quando o sujeito muda | Subject, ConcreteSubject, Observer, ConcreteObserver | Mediator, publish/subscribe |
| State | Comportamental | O objeto muda de comportamento quando seu estado interno muda | Context, State, ConcreteState | Strategy |
| Strategy | Comportamental | Família de algoritmos intercambiáveis e encapsulados | Strategy, ConcreteStrategy, Context | State, Template Method, Bridge |
| Visitor | Comportamental | Operação sobre os elementos de uma estrutura sem mudar suas classes (double dispatch) | Visitor, ConcreteVisitor, Element, ConcreteElement, ObjectStructure | Iterator, Composite |

## 6. Como registrar

1. Antes da sessão, gere o formulário de cada sistema:
   `python caderno/avaliar_sistema.py --somente-formulario --padrao Strategy --dupla "Nome da dupla"`
   ou, se tiver acesso ao projeto da outra dupla, rode o roteiro automaticamente com `--projeto`.
2. Faça as perguntas exatamente como estão no formulário (são as do roteiro da professora).
3. Copie a resposta integral (ou cole a saída do terminal) e preencha as quatro notas com
   uma justificativa curta citando o trecho.
4. Registre o tempo de resposta: ele faz parte da experiência de uso.
5. Ao final, preencha pontos fortes e fracos de cada sistema.
