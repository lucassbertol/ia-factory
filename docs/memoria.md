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
  - `intencao`: finalidade do turno, incluindo `avaliacao` de tentativa
  - `exercicio_pendente`: enunciado da atividade atual, ou string vazia

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

O classificador recebe tambem a ultima intencao e a indicacao de exercicio
pendente. Tentativas como "Minha resposta...", correcoes como "Agora eu..."
e continuacoes curtas como "Sim" ou "E por que?" sao encaminhadas considerando
esse estado. Durante a pratica, a intencao `avaliacao` seleciona somente
Inquiridor e Guardiao; os termos presentes no codigo da tentativa nao ativam
outros agentes. As instrucoes pedem feedback sobre a atividade existente,
sem propor outra nem presumir acerto de uma resposta ambigua.

Pedidos explicitos de explicacao ou exemplo podem intercalar a pratica sem
apagar o enunciado. Um novo pedido de exercicio substitui a atividade; um
fechamento ou "Encerrar exercicio" a encerra. O estado e gravado somente apos
uma resposta valida: recusas e falhas do modelo nao o alteram. O roteamento
continua heuristico, sem garantia de interpretar toda formulacao livre.

JSONs antigos continuam aceitos: na ausencia dos campos novos, a intencao e
inferida das perguntas anteriores e a atividade e recuperada quando possivel.

## 3. Memoria != conhecimento factual

Um ponto critico da estrategia: informacoes ditas pelo modelo em turnos
anteriores **nao sao tratadas automaticamente como verdade**. O Guardiao
reavalia a confiabilidade de tudo a cada turno. Isso evita que o sistema
consolide alucinacoes anteriores como fatos.

## 4. Limites da memoria

- Apenas os turnos mais recentes sao injetados (limite de caracteres), para
  nao exceder o tamanho de contexto do modelo local (qwen2.5:3b).
- O limite inclui o cabecalho. Ate metade dele e reservada ao enunciado
  pendente; o restante recebe os turnos recentes. Textos longos podem ser
  truncados no contexto, mas o conteudo integral permanece no JSON.
- A memoria e por sessao; ao encerrar o modo interativo (`sair`), a sessao
  permanece em disco e pode ser retomada informando o mesmo `sessao_id`.
- No modo de execução unica (`python -m agente "pergunta"`), o `sessao_id`
  e `default` por padrao.
- O modo interativo usa `interativo` por padrao. `--sessao ID` seleciona a
  mesma conversa em ambos os modos. `--sessao ID --limpar-sessao` remove o
  historico e a atividade apenas daquela sessao, encerrando sem chamar o modelo.
- IDs aceitam de 1 a 64 letras ASCII, numeros, `_` e `-`. A persistencia
  pressupoe uso sequencial, sem escritores concorrentes na mesma sessao.

## 5. Testes de memoria (Etapa 5)

`test_memoria.py` executa cenarios com o modelo para inspecao pedagogica:
  - Varios turnos na mesma sessao.
  - Contexto anterior utilizado de maneira coerente.
  - Exercicios com continuidade entre turnos.
  - Memoria nao tratada como conhecimento factual (reavaliacao pelo Guardiao).

`test_continuidade.py` verifica automaticamente fluxo, roteamento, CLI e arquivos
JSON em diretorios temporarios, com a chamada ao modelo substituida por respostas
controladas. Ele nao comprova a correcao conceitual das respostas de um LLM.
