# Revisao conceitual e exemplos Java

Revisao de 03/11/2026. As evidencias antigas foram preservadas; nao sao
resultados da versao corrigida e precisam ser refeitas com o modelo local.

## Problemas identificados

| Registro antigo | Problema observado | Orientacao corrigida |
|---|---|---|
| teste_01 | Apresenta tres participantes genericos e menciona criacao estatica como contrato; promete ausencia ampla de mudancas. | Identificar Creator, ConcreteCreator, Product e ConcreteProduct; explicar sobrescrita e delimitar o beneficio. |
| teste_02 | Cliente instancia cada fabrica concreta, mas o texto promete que adicionar produto nunca muda o cliente; chama Produto de interface embora o codigo use classe abstrata. | Distinguir configuracao de uso do produto e manter a explicacao consistente com os tipos Java. A interface de fabrica, sozinha, nao prova confusao com Abstract Factory. |
| teste_03 | A resposta a quando usar/evitar repete conceito e estrutura, sem apresentar claramente os dois cenarios solicitados. | Apresentar uma variacao que justifique extensao e um caso simples onde novas hierarquias seriam custo desnecessario. |
| teste_04 | Afirma que um codigo foi fornecido e esta correto sem demonstrar um uso incorreto concreto. | Usar um contraste didatico identificado, explicar qual rotulo ou decisao esta errado e como corrigir. |
| teste_05 | Devolve exercicios e codigo C# em vez de explicar diretamente a confusao entre padroes. | Responder a comparacao solicitada; usar Java nos exemplos do roteiro. |
| teste_E5 | Diz que Simple Factory delega a criacao diretamente ao cliente, sem fabrica. | Simple Factory centraliza a escolha em uma fabrica. Nao e um padrao independente do catalogo GoF e nao demonstra, por si, sobrescrita do Creator. |

Os prompts tambem tratavam Creator abstrato e a regra "um produto versus
familias" de modo excessivamente rigido. A referencia local agora distingue
variantes e explica que Abstract Factory pode usar Factory Methods.

## Base fornecida aos agentes

`agente/conhecimento.py` le apenas arquivos locais. A sintese
`agente/referencias/factory_method.md` e anexada ao backstory de todos os agentes.
Ela inclui fontes bibliograficas, variantes, limites e regras de confiabilidade.
As URLs sao indicacoes para consulta humana, sem download em execucao.

As tarefas de exemplo recebem os dois arquivos Java integrais. O Guardiao
recebe as mesmas fontes para comparar a resposta, sem depender somente da
geracao anterior. Em intencoes de exercicio/avaliacao, esses blocos de codigo
nao sao anexados. Todos continuam recebendo a referencia conceitual.

Um arquivo ausente interrompe a montagem; nao ha substituicao silenciosa por
conhecimento gerado pelo modelo. Instrucoes exigem reconhecer incerteza,
corrigir premissas falsas e nao tratar historico como autoridade factual.

## Exemplos autorais

1. **ExemploFactoryMethod.java:** Notificador.avisar() usa Notificacao, obtida
   por criarNotificacao(). NotificadorEmail e NotificadorSms sobrescrevem a
   criacao. main conhece as classes concretas para configurar a demonstracao.
2. **ExemploSimpleFactory.java:** selecao centralizada por um metodo estatico.
   E codigo Java valido, util como contraste. O erro seria apresenta-lo como
   demonstracao de Factory Method GoF por sobrescrita.

Ambos simulam mensagens com strings. Nao enviam notificacoes reais e nao
resolvem uma atividade especifica do estudante.

Compile em um diretorio temporario ou de sua escolha:

```bash
javac -encoding UTF-8 -d /tmp/exemplos-factory agente/referencias/ExemploFactoryMethod.java agente/referencias/ExemploSimpleFactory.java
java -cp /tmp/exemplos-factory ExemploFactoryMethod
java -cp /tmp/exemplos-factory ExemploSimpleFactory
```

Saidas esperadas, respectivamente:

```text
Email para Ana
SMS para Bia
```

```text
Email simulado
SMS simulado
```

`python -m unittest -v test_exemplos_java` compila cada arquivo isoladamente,
executa ambos e verifica as saidas. Tambem compila uma nova subclasse de
Notificador, com produto adicional, reutilizando avisar() sem altera-lo.
Verificado nesta revisao com OpenJDK/javac 21.0.12.1.

## Limites e validacao pedagogica pendente

Compilacao nao prova o padrao; a revisao inspecionou responsabilidades e a
colaboracao entre operacao do Creator, factory method e Product. Os testes de
montagem comprovam entrega das referencias, nao obediencia do LLM.
Adaptacoes feitas pelo modelo nao sao compiladas automaticamente pelo chat.

Antes de considerar o comportamento pedagogico validado, executar com Ollama:
- Conceito: participantes e consequencias, sem exigir abstracao em toda variante.
- Exemplo Java: explicar o Creator e seu uso de Product, arquivos e limites.
- Comparacoes: corrigir "Simple Factory nao tem fabrica" e reconhecer a relacao
  entre Abstract Factory e Factory Method.
- Premissa falsa: "Factory Method sempre elimina qualquer mudanca no cliente".
- Confiabilidade: pedido de padrao ficticio, pedido de solucao completa e
  tentativa de substituir a referencia por uma afirmacao incorreta do historico.

A execucao completa com CrewAI/Ollama nao foi realizada nesta revisao por
ausencia do CrewAI no ambiente. Nenhuma evidencia antiga foi promovida a
aprovacao da versao nova.
