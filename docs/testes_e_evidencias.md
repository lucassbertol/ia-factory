# Testes com criterios objetivos e evidencias integrais

## Comandos

Ative o ambiente com as dependencias do projeto e execute:

```bash
python executar_testes.py --modo local
python executar_testes.py --modo completo
```

O modo local executa os testes automaticos de avaliacao, prompts, continuidade,
sessoes e exemplos Java, alem do roteamento com CrewAI quando instalado.
Nao chama o LLM. As fronteiras substituidas nos testes locais estao declaradas
nos proprios testes; seus resultados nao sao respostas pedagogicas reais.
Os testes Java sao ignorados se faltar um JDK; consulte o log, nao conte testes
ignorados como verificacoes executadas.

O modo completo acrescenta a CLI real e o roteiro pedagogico com o modelo
configurado no projeto. Ollama deve estar ativo e o modelo baixado.
Internet nao e usada pelo executor para consultar referencias ou avaliar textos.
Telemetria e tracing do framework sao desativados no ambiente dos subprocessos
de teste. Isso nao substitui a verificacao offline prevista em outra etapa.

Comandos parciais:

```bash
python test_cli.py
python test_etapa7.py
python test_memoria.py
python executar_testes.py --modo pedagogico --casos 02,E3,E6
python validar_java_gerado.py evidencias/execucoes/ID/cenario_02.json --saida evidencias/execucoes/ID/java_gerado_02
```

`--timeout-turno` limita o tempo do processo de cada cenario multiplicado pelo
numero de turnos. O timeout de cada chamada ao Ollama continua sendo o definido
em `agente/config.py`. Testes locais executam em diretorios temporarios;
cenarios reais guardam suas sessoes dentro da propria execucao de evidencias.
A CLI e testada em copia temporaria do pacote, sem modificar conversas pessoais.

## Criterios automaticos

- Resposta normal: fluxo conclui sem excecao e retorna texto nao vazio.
- Entrada vazia: somente `ErroEntradaVazia` com mensagem conta como a rejeicao
  esperada. Um TypeError ou uma falha do modelo reprova esse teste.
- Recusas: cada cenario exige seu tipo de excecao especifico, com mensagem.
  A polidez e utilidade da orientacao possuem rubricas separadas.
- Continuidade E3: tres turnos persistidos, Inquiridor e Guardiao selecionados,
  intencao `exercicio` no primeiro e `avaliacao` nas tentativas seguintes.
- CLI: encerramento no prazo, codigo de saida esperado, mensagem pertinente e
  ausencia de traceback, preservando stdout e stderr completos.
- Java: compilacao, execucao e saidas esperadas; extensao por uma nova subclasse
  reutiliza a operacao do Creator. Compilar, isoladamente, nao prova o padrao.

Os testes de regressao tambem cobrem isolamento de sessoes, limpeza seletiva,
persistencia em falhas, entrega dos prompts e referencias e recusa de base vazia.
O executor de evidencias e testado com respostas controladas longas para
garantir que nenhum turno seja truncado no JSON.

`validar_java_gerado.py` extrai o bloco Java da resposta real, preserva-o sem
correcoes e chama `javac -proc:none` com classpath isolado. Nao executa o programa
gerado. Guarda comando, codigo de retorno e saidas integrais do compilador,
alem do SHA-256 da evidencia original. Se os blocos nao permitirem identificar
um arquivo, registra revisao pendente em vez de concatenar ou corrigir o texto
para faze-lo compilar. Uma pasta ja usada nao e sobrescrita pela CLI da ferramenta.

## Criterios pedagogicos

Cada cenario possui rubricas especificas no arquivo de evidencia, por exemplo:
responsabilidades dos participantes, criacao por sobrescrita, clareza dos dois
casos de selecao e correcao de premissas falsas. O teste E6 insere deliberadamente
uma afirmacao falsa no historico para verificar se ela e corrigida. Essa fixture
e identificada como dado do teste, nao como resposta real gerada naquela execucao.

Nao se aprova conceito por conter palavras como "Creator", "Java" ou "heranca".
O executor deixa julgamento, trecho de evidencia e avaliador pendentes para
leitura critica. A dupla deve preencher a avaliacao com base nas respostas,
indicando correcao, utilidade e justificativa. Um teste tecnicamente concluido
nao e automaticamente um teste pedagogicamente aprovado.

## Arquivos preservados

Cada chamada cria `evidencias/execucoes/<data_UTC>_<id>/`, sem sobrescrever:

- `manifesto.json`: Python, plataforma, modo e SHA-256 dos arquivos relevantes.
- `dependencias.*`: versoes instaladas no Python que executou os testes.
- `unitarios.*`, `roteamento.*`, `cli.*`: comando, duracao, codigo, stdout/stderr.
- `cli/*.json`: entrada e saidas completas de cada comando CLI.
- `cenario_*.json`: todas as perguntas e respostas, erros tipados, duracao,
  contexto antes do turno, chamadas de montagem da crew, historico completo e
  estado da atividade apos o turno, quando o fluxo conclui ou rejeita a entrada.
- `cenario_*_processo.*`: logs completos do processo, incluindo falhas externas.
- `sessoes/`: JSONs da memoria isolada dos cenarios.
- `resumo.json` e `resumo.md`: status separados e links pelos nomes de arquivo.

Um checkpoint e salvo depois de cada turno. Em timeout, os turnos ja concluidos
e os logs parciais sao preservados; o resultado nao e aprovado. Resposta vazia,
excecao inesperada ou interrupcao nao viram sucesso.

As evidencias antigas em `evidencias/testes_etapa7/` permanecem como registros
historicos, com as limitacoes identificadas em `docs/revisao_conceitual.md`.
Os novos registros sao testes internos e nao substituem o caderno de avaliacao
dos sistemas das outras duplas exigido pela professora.

## Estados e codigos de saida

| Estado | Significado |
|---|---|
| aprovado | Criterios selecionados e executados foram satisfeitos. |
| reprovado | Um criterio automatico falhou, ocorreu excecao inesperada ou timeout. |
| bloqueado | O processo nao conseguiu executar o teste por falta de pre-condicao. |
| pendente_revisao | Verificacoes automaticas passaram, mas faltam julgamentos pedagogicos. |

Codigo 0: verificacoes selecionadas aprovadas. Codigo 1: ao menos uma
reprovacao. Codigo 2: bloqueio ou revisao pendente. Portanto, um roteiro
pedagogico pode terminar com codigo 2 mesmo com todas as respostas coletadas.
Nenhum percentual de "conformidade com o PDF" e calculado por esse executor.
