# Estrategia de Memoria da Conversa

Projeto final ELC1070 — Sistema Multiagente Pedagógico (Factory Method).

## 1. Onde a memoria e armazenada

A conversa e persistida em arquivos JSON, um por sessao, no diretório
`memoria/sessoes/<id_sessao>.json`. Cada arquivo contem uma lista de turnos,
com os campos:
  - `timestamp`: data/hora do turno (ISO 8601)
  - `pergunta`: texto digitado pelo estudante
  - `resposta`: resposta gerada pelo sistema
  - `agente`: ultimo agente que participou (tutor, exemplificador, inquiridor ou guardiao)

Os arquivos sao criados automaticamente em tempo de execucao pelo modulo
`agente/memoria.py` (`MemoriaConversa`).

## 2. Como a memoria e usada

A cada chamada da CLI (`python -m agente "pergunta"`):

1. O sistema carrega o historico da sessao informada (ou `default`/`interativo`).
2. O historico recente e convertido em texto (respectando um limite de
   `MAX_CONTEXTO_CARACTERES`, configurado em `agente/config.py`).
3. Esse texto e injetado como contexto nos prompts dos agentes, de modo que
   o dialogo permaneça coerente ao longo de varios turnos (ex.: o estudante
   responde a um exercicio proposto anteriormente e o Inquiridor avalia a
   resposta tendo em vista o exercicio original).

## 3. Memoria != conhecimento factual

Um ponto critico da estrategia: informacoes ditas pelo modelo em turnos
anteriores **nao sao tratadas automaticamente como verdade**. O Guardiao
reavalia a confiabilidade de tudo a cada turno. Isso evita que o sistema
consolide alucinacoes anteriores como fatos.

## 4. Limites da memoria

- Apenas os turnos mais recentes sao injetados (limite de caracteres), para
  nao exceder o tamanho de contexto do modelo local (qwen2.5:3b).
- A memoria e por sessao; ao encerrar o modo interativo (`sair`), a sessao
  permanece em disco e pode ser retomada informando o mesmo `sessao_id`.
- No modo de execução unica (`python -m agente "pergunta"`), o `sessao_id`
  e `default` por padrao.

## 5. Testes de memoria (Etapa 5)

Os testes estao em `test_memoria.py` e validam:
  - Varios turnos na mesma sessao.
  - Contexto anterior utilizado de maneira coerente.
  - Exercicios com continuidade entre turnos.
  - Memoria nao tratada como conhecimento factual (reavaliacao pelo Guardiao).
