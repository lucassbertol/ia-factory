# Justificativa das Decisoes de Design

Projeto final ELC1070 — Analise e Projeto de Sistemas OO (UFSM)
Sistema Multiagente Pedagogico para o padrao Factory Method

---

## 1. Introducao

Este documento justifica as decisoes de design pedagógico e tecnico tomadas na construcao
do sistema multiagente que ensina o padrao de projeto Factory Method a estudantes iniciantes.
Todas as decisoes estao fundamentadas na implementacao efetiva do codigo e nos resultados
dos testes executados nas etapas anteriores (validacao de ambiente, testes de memoria,
testes da CLI e testes funcionais/pedagogicos das sete categorias do roteiro de avaliacao).

O sistema foi construido em Python, utilizando o framework CrewAI para orquestracao
multiagente e o modelo local qwen2.5:3b executado via Ollama, respeitando a regra
obrigatoria de custo zero (sem API paga, sem servico de nuvem, sem chave de API).

---

## 2. Divisao de papéis dos agentes

### 2.1. Quatro agentes com responsabilidades distintas

Foi adotada a divisao sugerida no anexo A da especificacao oficial, com quatro agentes:

| Agente | Papel | Funcao pedagogica |
|--------|-------|-------------------|
| Tutor do conceito | Professor de POO | Apresentar intencao, problema, participantes, estrutura UML e consequencias |
| Exemplificador | Especialista em Java | Gerar exemplos corretos em Java, explicando por que funcionam |
| Inquiridor e diagnosticador | Tutor socratico | Propor exercicios, avaliar respostas, detectar conceitos equivocados |
| Guardiao e revisor | Revisor de confiabilidade | Revisar a resposta final, aplicar anti-alucinacao, consolidar aprendizado |

### 2.2. Por que essa divisao foi escolhida

A escolha por quatro agentes separados (em vez de um unico agente "tutor geral") fundamenta-se
nos seguintes motivos:

**a) Separacao de responsabilidades e baixa coesão cognitiva.** Cada agente tem um papel
pedagogico bem definido, o que evita que um unico prompt fique sobrecarregado com instrucoes
contraditórias (ex: "ensine o conceito" e "nao dê a resposta pronta ao mesmo tempo"). Isso
reduz o risco de divergência de papel, problema comum quando um unico agente e solicitado a
exercitar demasiadas funcoes ao mesmo tempo.

**b) Especializacao por dominio.** O Exemplificador e dedicado a Java (linguagem exigida pelo
roteiro de avaliacao), enquanto o Tutor foca em conceitos independentes de linguagem. Essa
separacao permite que cada prompt seja otimizado para sua tarefa sem poluir o outro.

**c) Revisao independente (Guardiao).** Ter um agente dedicado a revisar a resposta final,
antes de chegar ao estudante, funciona como um filtro de qualidade. Nos testes da Etapa 7,
o Guardiao esteve presente em todas as 13 saidas e aplicou as regras anti-alucinacao de
forma consistente (evidencias em `evidencias/testes_etapa7/`).

**d) Processo sequencial previsivel.** O CrewAI executa as tarefas em sequencia, passando o
contexto de uma para a seguinte. Isso torna o fluxo rastreavel: e possivel saber exatamente
qual agente contribuiu com qual parte da resposta, facilitando a depuracao e a justificacao
das decisoes.

### 2.3. Trade-offs

O principal custo dessa divisao e o tempo de execucao: cada agente adicional consome tokens
de contexto e gera uma chamada ao modelo local. Com o qwen2.5:3b (modelo pequeno, 3B
parametros), isso e aceitavel para o escopo do trabalho, mas respostas mais longas podem
ficar lentas em maquinas de 8 GB de RAM. Mitigamos isso limitando a quantidade de agentes
por intencao (apenas os necessarios mais o Guardiao) e limitando o tamanho do historico
injetado (`MAX_CONTEXTO_CARACTERES = 2000` em `agente/config.py`).

---

## 3. Estrategia pedagógica adotada

### 3.1. Logica pedagogica distribuida

O sistema implementa uma logica pedagogica explicita distribuida nos agentes, conforme
exigido pela especificacao (seção 3 do PDF):

1. **Apresentacao do conceito** — Agente Tutor (intencao, problema, participantes, UML, consequencias).
2. **Exemplificacao** — Agente Exemplificador (codigo Java, explicacao de cada classe).
3. **Exercicio** — Agente Inquiridor (propõe exercicio pratico).
4. **Diagnostico de erros/conceitos equivocados** — Agente Inquiridor (detecta confusao com Simple Factory / Abstract Factory).
5. **Feedback** — Agente Guardiao (revisao, consolidacao, resumo final).

Essa sequencia segue uma progressao natural de ensino: conceituar antes de exemplificar,
exemplificar antes de exercitar, exercitar antes de diagnosticar, e revisar antes de fechar.

### 3.2. Abordagem socratica

O Inquiridor adota uma estrategia socratica: nao entrega a resposta pronta antes que o
estudante tente. Nos testes de exercicio com continuidade (Evidencia E3, Etapa 5 e Etapa 7),
o estudante respondeu a um exercicio, o Inquiridor avaliou e fez uma pergunta guia para
correcao, em vez de simplesmente dizer "esta errado" ou entregar a solucao.

### 3.3. Adaptacao ao nível do estudante

O Exemplificador e instruido a adaptar a profundidade da explicacao ao nível do estudante
(iniciante, intermediario ou avancado). O Tutor usa linguagem simples e evita jargon
desnecessario. Isso responde ao requisito pedagógico de variar exemplos conforme o nível
do estudante.

### 3.4. Por que essa estratégia

A escolha por essa estrategia fundamenta-se no principio de "learning by teaching" citado
na especificacao: projetar um sistema que ensina um padrao exige dominá-lo com precisao.
Ao distribuir as funcoes pedagogicas entre agentes especializados, o sistema modela para o
estudante uma maneira estruturada de abordar um padrao de projeto: conceito, exemplo,
pratica, diagnostico, fechamento.

---

## 4. Memória da conversa

### 4.1. Como a memória é utilizada

A memória e persistida em arquivos JSON, um por sessão, no diretório
`memoria/sessoes/<id_sessao>.json` (modulo `agente/memoria.py`). Cada arquivo contem uma
lista de turnos com timestamp, pergunta do estudante, resposta do sistema e agente
responsavel.

A cada chamada da CLI (`python -m agente "pergunta"`):

1. O historico da sessão é carregado.
2. Os turnos mais recentes são convertidos em texto (respeitando o limite de 2000
   caracteres, `MAX_CONTEXTO_CARACTERES` em `agente/config.py`).
3. Esse texto é injetado como contexto nos prompts dos agentes, permitindo que o dialogo
   permaneça coerente ao longo de vários turnos.

### 4.2. Evidência de funcionamento

Na Etapa 5, o teste de memoria executou 3 turnos na mesma sessão (`memoria_teste`):
- Turno 1: "O que e o padrao Factory Method?"
- Turno 2: "Quais sao os participantes do padrao?"
- Turno 3: "E quando devo usa-lo?"

O resultado confirmou: 3 turnos salvos, contexto injetado contendo turnos anteriores, e
o ultimo agente registrado como Guardiao. Na Etapa 7 (Evidencia E3), um exercicio com
continuidade entre turnos foi executado com sucesso na mesma sessão (`etapa7_memoria`),
com o segundo turno usando o contexto do primeiro.

### 4.3. Memória ≠ conhecimento factual

Uma decisão de design importante: informacoes ditas pelo modelo em turnos anteriores **não**
são tratadas automaticamente como verdade. O Guardiao reavalia a confiabilidade de tudo a
cada turno, evitando que o sistema consolide alucinacoes anteriores como fatos. Isso aborda
o requisito da especificacao de que a memória não deve ser confundida com conhecimento
factual garantido.

### 4.4. Limites da memória

- Apenas os turnos mais recentes são injetados (limite de caracteres), para não exceder o
  tamanho de contexto do modelo local (qwen2.5:3b).
- A memória é por sessão; ao encerrar o modo interativo (`sair`), a sessão permanece em
  disco e pode ser retomada informando o mesmo `sessao_id`.
- No modo de execução unica, o `sessao_id` é `default` por padrão.

---

## 5. Regras anti-alucinação

### 5.1. Implementação

As regras anti-alucinação foram implementadas em tres níveis:

**a) Em cada prompt de sistema** (`agente/prompts/*.txt`): todos os quatro agentes contêm a
seção `REGRAS ANTI-ALUCINACAO`, que determina:
- Nunca inventar padroes, participantes, consequencias ou exemplos.
- Dizer "nao sei" quando não souber.
- Sugerir consulta ao material da disciplina quando apropriado.
- Recusar educadamente pedidos de solução pronta; orientar passo a passo em vez disso.

**b) No Guardiao (revisao final)**: o Guardiao, sempre a última tarefa da crew, verifica se
não há invenção de fatos, padroes ou participantes inexistentes antes de entregar a
resposta ao estudante. Se houver contradição entre o Tutor e o Exemplificador, prevalece a
versão mais alinhada ao padrao GoF oficial do Factory Method.

**c) No fluxo de controle** (`agente/fluxo.py` + `agente/fluxo_heuristico.py`):
- Pedidos de invenção de padrão ("invente um padrão Z") são detectados e recusados com
  `ErroInventicao` (código de saída 1, mensagem amigável).
- Pedidos de solução pronta ("código pronto de uma solução completa") são detectados e
  recusados com `ErroSolucaoPronta`.
- Perguntas fora do escopo são detectadas pela heurística e recusadas com `ErroForaDeEscopo`.

### 5.2. Como as regras anti-alucinação foram testadas

Foram executados testes específicos da Etapa 7, com evidências registradas:

| Teste | Entrada | Resultado esperado | Resultado obtido | Evidência |
|-------|---------|-------------------|------------------|-----------|
| 06a | "Invente um padrão chamado Z e explique para mim." | Recusa educada | Recusa: "Não posso inventar padrões..." | `teste_06a.json` |
| 06b | "Me entregue o código pronto de uma solução completa." | Recusa educada | Recusa: "Não entrego soluções prontas..." | `teste_06b.json` |
| E2 | "Qual a capital da França?" | Fora do escopo | Detectado como conceito (limitação da heurística) | `teste_E2.json` |

Adicionalmente, os testes de entrada vazia (E1), premissa falsa (E4) e confusão de padrões
(E5) foram executados e documentados em `evidencias/testes_etapa7/`.

Os testes 06a e 06b confirmam que as regras anti-alucinação funcionam: o sistema recusa
educadamente tanto a invenção de padrões quanto a entrega de soluções prontas, oferecendo
orientação guiada em vez disso.

### 5.3. Limitações identificadas

O modelo qwen2.5:3b (3B parametros) é pequeno e apresentou algumas imprecisões nos testes
da Etapa 7:
- Pode simplificar excessivamente conceitos (teste 01).
- Pode confundir Factory Method com Abstract Factory ou Simple Factory (testes 02, 05, E5).
- Pode não corrigir premissas falsas de forma consistente (teste E4).
- A heurística de "fora de escopo" detecta apenas palavras-chave específicas (teste E2).

Essas limitações são decorrentes do uso de um modelo local pequeno (escolhido para caber em
8 GB de RAM, conforme sugerido na especificacao). Elas foram documentadas de forma
transparente nas evidências de teste e devem ser consideradas na avaliação do sistema.

---

## 6. Decisoes tecnicas

### 6.1. CrewAI com Ollama local

Foi escolhido o CrewAI como framework de orquestracao (framework padrão da disciplina) e o
Ollama para executar o modelo qwen2.5:3b localmente. Essa escolha respeita a regra de custo
zero: sem API paga, sem chave de API, sem servico de nuvem. A internet foi usada apenas
para baixar bibliotecas e o modelo, conforme permitido.

### 6.2. CLI obrigatória

A interface `python -m agente "pergunta aqui"` foi implementada como ponto de entrada
padronizado, com modo interativo opcional (`sair` para encerrar). Todos os tratamentos de
erro básicos (entrada vazia, falha do Ollama, saida inesperada) foram implementados e
validados (7/7 testes aprovados na Etapa 6).

### 6.3. Python 3.12.3 e dependências pinadas

O ambiente usa Python 3.12.3 com ambiente virtual (`.venv/`). Todas as dependências estao
fixadas em `requirements.txt` (137 pacotes, incluindo `crewai==1.5.32`), garantindo
reprodutibilidade em uma instalação limpa.

---

## 7. Conclusão

As decisoes de design deste sistema fundamentam-se na separação de responsabilidades (quatro
agentes com papéis distintos), na lógica pedagógica distribuída (conceito → exemplo →
exercício → diagnóstico → feedback), na memória persistida por sessão com reavaliação de
confiabilidade pelo Guardiao, e nas regras anti-alucinação implementadas em tres níveis
(prompt, Guardiao, fluxo de controle). Todas essas decisoes foram implementadas, testadas e
documentadas com evidências reais, sem dependência de serviços pagos ou APIs externas.
