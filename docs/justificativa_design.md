# Justificativa das decisões de design

Versão em Markdown da seção 3 do relatório de entrega.

## 3.1. Divisão de papéis entre os agentes

Partimos da divisão sugerida no Anexo A, porque ela cobre as funções exigidas (ensinar, exemplificar, exercitar e diagnosticar, garantir confiabilidade), e a ajustamos ao que observamos com um modelo de 3B. **Tutor e Inquiridor ficaram separados** porque têm posturas opostas: o Tutor explica, o Inquiridor não pode dar a resposta. Num prompt único, essas regras competem; no teste de 28/10, por exemplo, uma pergunta de comparação foi respondida com um exercício. O **Exemplificador** ficou separado porque a responsabilidade dele mudou: em vez de escrever código, ele explica código verificado.

A mudança mais importante foi no **Guardião**. Na primeira versão ele reescrevia a resposta final. Nas evidências de 03/11, a reescrita por um modelo pequeno perdia conteúdo e introduzia erros novos (o cenário 05 afirmou que o Factory Method 'é confundido com o Factory Method'). Agora ele é um **verificador**: devolve um veredito objetivo, e quem corrige é o autor. Isso separa a responsabilidade de produzir da de conferir, como numa revisão de código.

As coletas com o modelo real levaram a uma segunda decisão. Mesmo como verificador, o Guardião de 3B reprovou quase todas as respostas com problemas inexistentes. Exigimos que cada problema citasse um trecho real e explicasse o erro, o que descartou a maioria; ainda assim, nas três coletas de 04/11 nenhuma reescrita pedida por ele corrigiu um erro real, e 7 pioraram a resposta (por exemplo, 'Desculpe pela confusão anterior' e frases repetidas). Por isso a reescrita ficou **desligada por padrão**: o Guardião continua conferindo cada resposta, e o veredito fica registrado na memória e nas evidências para a dupla auditar, mas a correção efetiva fica com os guardrails determinísticos, que nas mesmas coletas pegaram erros reais (premissa falsa, laços, afirmações contra o GoF). O trade-off é aceito conscientemente: um verificador fraco que reescreve é pior do que um verificador que apenas registra.

**Alternativas consideradas:** (a) um único agente com todas as regras, rejeitado porque o prompt fica longo e mistura papéis; (b) o processo hierárquico do CrewAI, com um agente gerente decidindo quem responde, rejeitado porque acrescenta uma chamada ao modelo por turno e um modelo de 3B não é confiável como roteador; (c) executar os quatro agentes em todo turno (nossa primeira versão), rejeitado pelo tempo de 4 chamadas seguidas e pelas contradições entre agentes. Ficamos com um roteador determinístico e um autor por turno. O custo é a rigidez: uma formulação inesperada pode ir para o agente errado.

## 3.2. Estratégia pedagógica

A estratégia segue a progressão pedida na especificação, mas o estudante escolhe a ordem: **conceito em camadas** (ideia central, problema, participantes, consequências), **exemplo trabalhado**, **exercício socrático**, **diagnóstico de equívocos** e **feedback**. Toda resposta termina com uma pergunta que convida o próximo passo, porque um tutor que só responde transforma a conversa em consulta.

Os exemplos em Java são **verificados**: quatro arquivos que compilamos e executamos (`ExemploFactoryMethod`, `ExemploFactoryMethodPadrao`, `ExemploUsoIncorreto` e `ExemploSimpleFactory`), exibidos com a saída real. Escolhemos isso depois de ver que o código gerado pelo modelo não compilava (validação com `javac` do cenário 02 em 03/11) ou vinha em C#. Para o uso incorreto, o código **compila mas está errado**: `avisar()` ignora o factory method, e `NotificadorSms` imprime 'Email para Bia'. O estudante vê a consequência concreta do erro antes da correção de uma linha.

Os **exercícios** seguem a mesma lógica dos exemplos: vêm de um banco de três enunciados verificados (identificar participantes, distinguir Simple Factory e estender um exemplo), cada um com gabarito. A quarta coleta mostrou por quê: o exercício criado pelo modelo trocava PDF com CSV e já entregava a solução. O Inquiridor recebe o gabarito, que nunca é mostrado, para avaliar a tentativa com base nele, e não no que o modelo imagina ser a resposta.

Os equívocos tratados vêm da literatura e dos nossos testes: confundir com Simple Factory (que não é padrão GoF e não usa sobrescrita), com Abstract Factory (famílias de produtos), achar que Creator precisa ser abstrato (o segundo exemplo usa um Creator concreto) e achar que o `new` desaparece. O nível declarado muda a linguagem e o primeiro exemplo mostrado.

## 3.3. Uso da memória

A memória é um arquivo JSON por sessão (`--sessao ID`), que persiste até `--limpar-sessao`. Persistir em disco é necessário porque o comando obrigatório encerra após cada pergunta. Cada turno guarda pergunta, resposta, intenção, agentes, veredito do Guardião, exercício em andamento, nível e exemplo mostrado.

Ela é usada para a continuidade didática: avaliar uma tentativa contra o enunciado salvo, mesmo depois de vários turnos; não repetir o mesmo exemplo quando o estudante pede outro; manter a linguagem no nível declarado; e fazer um fechamento que retoma os tópicos estudados. Não usamos a memória nativa do CrewAI porque ela depende de um modelo de embeddings que, sem configuração, é o da OpenAI, o que exigiria chave de API e quebraria a regra de custo zero.

Para **não perpetuar respostas incorretas**, o histórico entra no prompt marcado como 'dados, não instruções'; a referência local continua sendo a base factual; o código das respostas anteriores é omitido do contexto; o histórico só é enviado quando a pergunta depende dele; e o Guardião não recebe o histórico, porque julga a resposta só contra a referência.

## 3.4. Prevenção de alucinações e validação das respostas

Usamos **defesa em camadas**, porque nenhuma camada sozinha é confiável com um modelo de 3B:

- **Barreiras determinísticas, antes do modelo.** Pedidos para inventar padrão, nomes de padrão desconhecidos (conferidos contra um catálogo com os 23 do GoF e outros conhecidos), outros padrões e pedidos de solução pronta, inclusive disfarçados ('escreva um sistema completo para eu entregar'), recebem resposta fixa. A recusa explica o motivo e oferece um caminho: para solução pronta, cinco passos para o estudante construir a sua.
- **Prompts com base factual.** Cada agente recebe a referência local, regras para dizer 'não sei com segurança' e um exemplo de resposta boa. Comparações com outros padrões recebem a intenção verificada desse padrão, para o modelo não 'lembrar' definições.
- **Guardrails determinísticos.** Regras criadas a partir de erros reais das nossas evidências: ConcreteProduct sobrescrevendo o factory method, Simple Factory como padrão GoF, Creator obrigatoriamente abstrato, código em outra linguagem, links e respostas longas.
- **Guardião.** Checklist de oito itens e veredito registrado. Cada problema apontado precisa citar, entre aspas, um trecho que exista na resposta e explicar o erro; os demais são descartados. A reescrita pedida por ele está desligada por padrão (ver 3.1); na segunda tentativa do guardrail, frases com erro factual conhecido são removidas.
Uma correção técnica reduziu as alucinações na origem. O CrewAI 1.15 conecta o Ollama por um endpoint compatível com a OpenAI que não permite definir a janela de contexto; com a janela padrão, o início do prompt (persona, regras e referência) era cortado. Criamos um LLM próprio (subclasse de `BaseLLM`) que chama `/api/chat` com num_ctx 8192; também baixamos a temperatura para 0.2, reduzindo a variação nas respostas conceituais.

**Verificação:** 39 testes automáticos (`tests/test_unitarios.py`) cobrem o roteiro e 19 variações de perguntas, as recusas, os guardrails, o veredito e a reescrita opcional do Guardião e as falhas do Ollama, usando um Ollama simulado que registra cada requisição. Com o modelo real, `tests/test_perguntas_pdf.py --extras` coleta as 8 perguntas do roteiro e 6 casos-limite; na coleta de 04/11, as 6 recusas foram corretas, mas o Guardião reprovou as 8 respostas com problemas inventados, e a reescrita chegou a copiar a falsidade 'o Factory Method não é GoF'. Isso levou à exigência de trecho citado descrita acima. Na segunda coleta, nenhuma resposta final trazia falsidade grave, a premissa falsa do E3 foi corrigida e o tempo médio caiu para 12 s. [completar: julgamento da dupla].

## 3.5. Síntese das principais decisões e limitações

- **Um autor por turno e um Guardião verificador:** menos chamadas e menos contradições; o custo é que perguntas mistas dependem do roteador.
- **Material verificado em vez de código gerado:** elimina código que não compila; o custo é ter só quatro exemplos.
- **Barreiras e roteamento determinísticos:** recusas confiáveis e testáveis; o custo é a rigidez diante de formulações livres.
- **Guardião que registra, mas não reescreve:** decisão tomada a partir de três coletas reais; o custo é que um erro que só o Guardião perceberia não é corrigido automaticamente, e sim apontado no registro.
- **Memória própria em JSON:** custo zero e controle do que entra no prompt; o custo é não haver busca semântica no histórico.
**Limitações remanescentes:** o modelo ainda pode errar em explicações livres, e o Guardião, que usa o mesmo modelo, pode não perceber; o tempo de resposta é de cerca de 10 s por pergunta (quarta coleta de 04/11); o sistema ensina apenas em português e só o Factory Method.

