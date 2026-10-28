# Justificativa das Decisoes de Design

Projeto final ELC1070 — Analise e Projeto de Sistemas OO (UFSM)
Sistema Multiagente Pedagogico para o padrao Factory Method

---

## 1. Introducao

Este documento justifica as decisoes de design pedagógico e tecnico do sistema
multiagente que ensina o padrao Factory Method a estudantes iniciantes. Todas as
decisoes estao fundamentadas na implementacao efetiva do codigo e nos resultados
dos testes executados (Etapas 5, 6 e 7).

O sistema usa Python 3.12.3, CrewAI 1.15.32 e o modelo local qwen2.5:3b via
Ollama, respeitando a regra de custo zero (sem API paga, sem nuvem, sem chave
de API).

---

## 2. Divisao de papeis dos agentes

Foi adotada a divisao sugerida no anexo A da especificacao, com quatro agentes:

| Agente | Papel | Funcao pedagogica |
|--------|-------|-------------------|
| Tutor do conceito | Professor de POO | Intencao, problema, participantes, estrutura UML, consequencias |
| Exemplificador | Especialista em Java | Exemplos corretos em Java, explicando por que funcionam |
| Inquiridor e diagnosticador | Tutor socratico | Exercicios, avaliacao de respostas, conceitos equivocados |
| Guardiao e revisor | Revisor de confiabilidade | Revisao final, anti-alucinacao, consolidacao |

### Por que essa divisao foi escolhida

**a) Separacao de responsabilidades.** Quatro agentes separados evitam que um
unico prompt fique sobrecarregado com instrucoes contraditórias (ex: "ensine o
conceito" e "nao entregue a resposta pronta"). Isso reduz a divergencia de papel,
problema comum quando um unico agente acumula demasiadas funcoes.

**b) Especializacao por dominio.** O Exemplificador e dedicado a Java (exigida
pelo roteiro de avaliacao), enquanto o Tutor foca em conceitos independentes de
linguagem.

**c) Revisao independente (Guardiao).** Um agente dedicado a revisar a resposta
final funciona como filtro de qualidade. Nos testes da Etapa 7, o Guardiao esteve
presente em todas as 13 saidas aplicando anti-alucinacao de forma consistente.

**d) Processo sequencial previsivel.** O CrewAI executa tarefas em sequencia,
passando contexto de uma para a seguinte, tornando o fluxo rastreavel e
depuravel.

### Trade-offs

O custo e o tempo de execucao: cada agente consome tokens de contexto e gera
uma chamada ao modelo local. Com o qwen2.5:3b (3B parametros, 8 GB de RAM),
isso e aceitavel, mas respostas longas podem ficar lentas. Mitigamos limitando
a quantidade de agentes por intencao (apenas os necessarios mais o Guardiao) e
limitando o historico injetado (`MAX_CONTEXTO_CARACTERES = 2000`).

---

## 3. Estrategia pedagogica adotada

O sistema implementa uma logica pedagogica explicita distribuida nos agentes,
conforme exigido pela especificacao (seção 3):

1. **Apresentacao do conceito** — Tutor (intencao, problema, participantes, UML, consequencias).
2. **Exemplificacao** — Exemplificador (codigo Java, explicacao de cada classe).
3. **Exercicio** — Inquiridor (propõe exercicio pratico).
4. **Diagnostico de erros** — Inquiridor (detecta confusao com Simple Factory / Abstract Factory).
5. **Feedback** — Guardiao (revisao, consolidacao, resumo final).

Essa sequencia segue a progressao natural: conceituar antes de exemplificar,
exemplificar antes de exercitar, exercitar antes de diagnosticar, revisar antes
de fechar.

### Abordagem socratica

O Inquiridor nao entrega a resposta pronta antes que o estudante tente. Nos
testes de exercicio com continuidade (Evidencia E3), o estudante respondeu a um
exercicio, o Inquiridor avaliou e fez uma pergunta guia para correcao.

### Adaptacao ao nível do estudante

O Exemplificador adapta a profundidade ao nível do estudante (iniciante,
intermediario ou avancado). O Tutor usa linguagem simples e evita jargon.
Isso responde ao requisito de variar exemplos conforme o nível do estudante.

---

## 4. Memória da conversa

A memoria e persistida em JSON por sessão (`memoria/sessoes/<id>.json`),
modulo `agente/memoria.py`. A cada chamada da CLI:

1. Carrega o historico da sessão.
2. Converte turnos recentes em texto (limite de 2000 caracteres).
3. Injeta como contexto nos prompts, mantendo o dialogo coerente entre turnos.

### Evidência de funcionamento

Etapa 5: 3 turnos na mesma sessão confirmados (contexto injetado com turnos
anteriores, ultimo agente = Guardiao). Etapa 7 (E3): exercicio com continuidade
entre turnos executado com sucesso.

### Memória ≠ conhecimento factual

Informacoes ditas pelo modelo em turnos anteriores **não** sao tratadas como
verdade. O Guardiao reavalia a confiabilidade a cada turno, evitando consolidar
alucinacoes anteriores como fatos.

### Limites

Apenas turnos recentes sao injetados (limite de caracteres). Memoria é por
sessão e permanece em disco apos encerrar o modo interativo.

---

## 5. Regras anti-alucinação

Implementadas em tres níveis:

**a) Prompts de sistema:** todos os 4 agentes contêm `REGRAS ANTI-ALUCINACAO`
(nunca inventar padroes/participantes/consequencias/exemplos; dizer "nao sei"
quando nao souber; recusar solucoes prontas e orientar passo a passo).

**b) Guardiao (revisao final):** ultima tarefa da crew, verifica invençao de
fatos/padroes/participantes inexistentes. Em caso de contradicao entre Tutor e
Exemplificador, prevalece a versao mais alinhada ao GoF oficial.

**c) Fluxo de controle:** `ErroInventicao` (inventar padrao Z) e
`ErroSolucaoPronta` (codigo pronto) sao detectados e recusados com mensagens
amigáveis.

### Como foram testadas

| Teste | Entrada | Resultado |
|-------|---------|-----------|
| 06a | "Invente um padrao Z" | Recusa educada (`teste_06a.json`) |
| 06b | "Codigo pronto de solucao completa" | Recusa educada (`teste_06b.json`) |

### Limitacoes identificadas

O modelo qwen2.5:3b (3B parametros) e pequeno e apresentou imprecisoes nos testes
da Etapa 7: simplificacao excessiva (teste 01), risco de confundir Factory Method
com Abstract Factory/Simple Factory (testes 02, 05, E5), nao correcao consistente
de premissas falsas (E4), e heurística limitada de "fora de escopo" (E2). Essas
limitacoes sao decorrentes do modelo local pequeno (escolhido para caber em 8 GB
de RAM) e estao documentadas nas evidências de teste.

---

## 6. Decisoes tecnicas

**CrewAI + Ollama local:** framework padrao da disciplina e modelo executado
localmente, respeitando a regra de custo zero. Internet usada apenas para baixar
bibliotecas e o modelo.

**CLI obrigatória:** `python -m agente "pergunta aqui"` com modo interativo
opcional (`sair` para encerrar). Tratamento de erros basico implementado e
validado (7/7 testes na Etapa 6).

**Python 3.12.3 + dependencias pinadas:** ambiente virtual com
`requirements.txt` (137 pacotes, incluindo `crewai==1.15.32`), garantindo
reprodutibilidade.

---

## 7. Conclusao

As decisoes de design fundamentam-se na separacao de responsabilidades (quatro
agentes com papeis distintos), na logica pedagogica distribuida
(conceito → exemplo → exercício → diagnóstico → feedback), na memoria persistida
por sessão com reavaliacao de confiabilidade pelo Guardiao, e nas regras
anti-alucinacao em tres níveis (prompt, Guardiao, fluxo de controle). Todas
foram implementadas, testadas e documentadas com evidências reais, sem
dependência de serviços pagos ou APIs externas.
