# Sistema multiagente pedagógico — Factory Method

Projeto final de **ELC1070 — Análise e Projeto de Sistemas OO** (UFSM).

Quatro agentes de IA, coordenados pelo **CrewAI**, ensinam o padrão **Factory Method** a
estudantes iniciantes. Tudo roda na própria máquina com **Ollama + qwen2.5:3b**: sem chave de
API, sem nuvem, sem custo por uso.

| Agente | Papel |
|---|---|
| **Tutor do conceito** | Intenção, problema, participantes, consequências, quando usar/evitar, comparações |
| **Exemplificador** | Explica exemplos Java **verificados** (compilados e executados pela dupla) |
| **Inquiridor** | Redige feedback a partir da avaliação dos exercícios em Python e esclarece equívocos |
| **Guardião** | Revisa o texto: aprova, pede correção fundamentada ou declara análise inconclusiva |

Pedidos para inventar padrões, nomes de padrões inexistentes, pedidos de solução pronta e
assuntos fora do escopo recebem uma recusa educada **sem chamar o modelo**, sempre com um
próximo passo. Detalhes: [arquitetura](docs/arquitetura.md), [agentes](docs/agentes.md),
[memória](docs/memoria.md).

---

## 1. Requisitos

- Python **3.12** (testado com 3.12.10 no Windows e 3.12.3 no Linux)
- **Ollama** instalado e aberto: https://ollama.com/download
- Modelo **qwen2.5:3b** (cerca de 2 GB); 8 GB de RAM bastam, 16 GB é o recomendado
- JDK (opcional), para compilar manualmente os blocos Java de `agente/referencias/factory_method.md`

## 2. Instalação

### Windows (PowerShell)

```powershell
cd "C:\caminho\para\ia-factory"
python -m venv .venv
.venv\Scripts\Activate.ps1          # se bloquear: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
ollama pull qwen2.5:3b
```

### Linux

```bash
cd ia-factory
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
ollama pull qwen2.5:3b              # com o Ollama rodando (ollama serve)
```

O `requirements.txt` contém dependências com versões fixas e marcadores por sistema
operacional (por exemplo, `uvloop` só no Linux e `pywin32` só no Windows). Ele é gerado a
partir de `requirements.in` com `uv pip compile requirements.in --universal -p 3.12`.

## 3. Execução

```bash
python -m agente "Explique o que é o padrão Factory Method e qual problema ele resolve."
```

Esse é o contrato obrigatório: a resposta é impressa e o programa encerra. Sem pergunta, abre
uma conversa no terminal (digite `sair` para encerrar):

```bash
python -m agente
```

Opções:

| Opção | Efeito |
|---|---|
| `--sessao ID` | inicia ou retoma uma conversa (o exercício em andamento é lembrado) |
| `--limpar-sessao` | apaga a sessão indicada; sem pergunta, encerra; com pergunta, inicia uma nova conversa |
| `--nivel iniciante\|intermediario\|avancado` | ajusta a linguagem e o primeiro exemplo (também detectado em "sou iniciante") |
| `--silencioso` | não mostra o progresso nem o tempo (que vão para a saída de erro) |

Exemplo de prática com memória:

```bash
python -m agente --sessao ana "Proponha um exercício de Factory Method"
python -m agente --sessao ana "Recibo seria o Product e ReciboPdf um ConcreteProduct"
python -m agente --sessao ana "Encerrar exercício"
```

Interface web opcional (a CLI continua sendo o ponto de entrada oficial):

```bash
python -m agente.web          # abra http://127.0.0.1:8000
```

Abra a interface pelo endereço do servidor, não pelo HTML diretamente. Use
`python -m agente.web --port 8001` para escolher outra porta. O servidor atende
somente no computador local.

As sugestões preenchem o campo sem enviar. **Novo chat** pede confirmação antes
de apagar a conversa atual. A mesma aba recupera o histórico ao recarregar.
O cronômetro mostra a espera e a média dos envios concluídos na aba; essa média
não é persistida e zera ao recarregar. O backend registra a duração do turno
separadamente na sessão. Falhas de envio não entram na média da interface.

### Roteiro da avaliação

```bash
python -m agente "Explique o que é o padrão Factory Method e qual problema ele resolve."
python -m agente "Dê um exemplo de aplicação do padrão Factory Method em Java."
python -m agente "Descreva uma situação em que o padrão Factory Method é a melhor escolha e uma em que ele deveria ser evitado, explicando o porquê."
python -m agente "Como o padrão Factory Method costuma ser aplicado de forma errada? Dê um exemplo de uso equivocado e explique como corrigir."
python -m agente "Com qual padrão o Factory Method é mais confundido? Explique a diferença entre eles e por que essa confusão acontece."
python -m agente "Invente um padrão chamado Z e explique para mim"
python -m agente "Me entregue o código pronto de uma solução completa"
python -m agente "O que devo lembrar antes de usar o padrão Factory Method?"
```

## 4. Configuração

Tudo em `agente/config.py`, com valores que podem ser trocados por variáveis de ambiente:

| Variável | Padrão | Por quê |
|---|---|---|
| `OLLAMA_MODEL` | `qwen2.5:3b` | modelo local |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | servidor local do Ollama |
| `OLLAMA_NUM_CTX` | `8192` | a janela padrão do Ollama cortava o início dos prompts |
| `OLLAMA_TEMPERATURA` | `0.2` | menos variação e menos invenção |
| `OLLAMA_NUM_PREDICT` | `800` | respostas curtas e mais rápidas |
| `OLLAMA_REPEAT_PENALTY` | `1.15` | evita laços de frases repetidas |
| `OLLAMA_TIMEOUT_SEGUNDOS` | `180` | limite por chamada |
| `MAX_REESCRITAS_GUARDIAO` | `1` | uma rodada de correção seguida de nova revisão; limitado a 0 ou 1. Zero não libera respostas reprovadas |
| `AGENTE_DEBUG` | vazio | `1` mostra os logs internos do CrewAI |

A telemetria e o rastreamento do CrewAI são desligados em `agente/__init__.py`. O sistema roda
sem internet depois de instalado; para conferir, desligue a rede e execute uma pergunta.

## 5. Coleta de respostas do roteiro

Com o Ollama ativo e o modelo baixado:

```bash
python tests/test_perguntas_pdf.py            # 8 perguntas do roteiro
python tests/test_perguntas_pdf.py --extras   # roteiro + 6 casos-limite
```

O coletor salva as respostas integrais em `evidencias/respostas_teste.json`, criando
a pasta quando necessário. Uma nova execução substitui esse arquivo. Os resultados
incluem intenção, agentes, revisão do Guardião e duração; o campo `julgamento`
deve ser preenchido pela dupla após ler as respostas. A coleta não avalia
automaticamente a correção pedagógica. Veja [instruções dos testes](tests/README.md).

## 6. Estrutura

```text
agente/
  __main__.py          CLI (python -m agente)
  fluxo.py             orquestração de um turno
  fluxo_heuristico.py  roteador de intenções e barreiras anti-alucinação
  crew.py              agentes, tarefas e crews do CrewAI
  avaliacao_exercicio.py avaliação dos exercícios cadastrados e próximo passo
  verificacao.py       guardrails determinísticos e leitura do veredito do Guardião
  llm.py               LLM local (Ollama /api/chat com num_ctx e temperatura)
  memoria.py           memória por sessão (JSON)
  recusas.py           recusas educadas e boas-vindas
  catalogo.py          nomes e intenções dos padrões GoF
  conhecimento.py      leitura e seleção das seções da referência
  agentes/             leitura de ROLE/GOAL/BACKSTORY dos prompts
  prompts/             prompt de sistema de cada agente (fonte única)
  referencias/         factory_method.md: conceitos, Java, UML e exercícios
  web.py               interface web opcional
tests/                 testes locais sem modelo e coletor do roteiro
docs/                  arquitetura, agentes, memória, justificativa, mini-relatório
frontend/              HTML/CSS/JS da interface web
```

## 7. Solução de problemas

| Problema | Solução |
|---|---|
| `[Erro] Não foi possível falar com o modelo local` | Abra o Ollama (no Windows, pelo menu Iniciar; no Linux, `ollama serve`) |
| `Modelo 'qwen2.5:3b' não encontrado` | `ollama pull qwen2.5:3b` |
| `ModuleNotFoundError: crewai` | Ative o `.venv` e rode `python -m pip install -r requirements.txt` |
| Acentos estranhos no terminal do Windows | Use o Windows Terminal ou rode `chcp 65001` antes |
| A primeira resposta demora muito | Normal: o modelo está sendo carregado na memória; as seguintes são mais rápidas |

## 8. Arquivos de documentação

1. Sistema: este repositório (`requirements.txt`, `README.md`, código em `agente/`)
2. Documentação dos agentes: `docs/agentes.md` e seção 2 do relatório
3. Justificativa de design: `docs/justificativa_design.md` e seção 3 do relatório
4. Mini-relatório: `docs/mini_relatorio.md` e seção 4 do relatório
5. Relatório de entrega: `docs/Relatorio_Entrega_FactoryMethod.docx`

Os relatórios ainda possuem campos para a dupla completar antes da entrega.

## 9. Editar o material didático

A fonte única é `agente/referencias/factory_method.md`: conceitos, UML, códigos
Java, saídas esperadas, fatos, correção e exercícios com gabaritos. `conhecimento.py`
só lê e seleciona esse conteúdo; não é necessário editar Python para mudar o texto.

Preserve os títulos `## [identificador] Título` e as cercas de código. Seções
vazias, duplicadas ou campos obrigatórios ausentes geram erro de leitura.
Os exemplos usam seções `exemplo:ID:arquivo`, `:titulo`, `:codigo`, `:saida` e
`:fatos` (esta última para os exemplos explicados). Para adicionar um exercício,
acrescente `exercicio:ID:enunciado` e `exercicio:ID:gabarito` com ID único e estável.
A ordem no arquivo define a ordem inicial dos exercícios. Não altere IDs já usados
em sessões. Reinicie a CLI/web depois de editar o arquivo.

O Python seleciona os conceitos conforme a intenção. Código e UML são exibidos
sem regeneração; explicações continuam sendo geradas pelo modelo. Pedidos de
exercício continuam recebendo o enunciado do banco, sem chamada ao modelo.
Nos exercícios com avaliador registrado em `agente/avaliacao_exercicio.py`, o
Inquiridor recebe os fatos avaliados pelo Python, sem gabarito. Um exercício novo
sem avaliador usa a avaliação pelo Inquiridor com gabarito reservado; adicionar
um enunciado ao Markdown não cria automaticamente um avaliador determinístico.

Para compilar um exemplo manualmente, copie o bloco `:codigo` para um arquivo
com o nome indicado em `:arquivo`, numa pasta temporária, e use `javac Nome.java`
e `java Nome`. A saída esperada está em `:saida`. Alterações no código exigem
nova compilação e conferência da saída antes de considerá-lo verificado.

Testes locais sem chamadas ao Ollama:

```bash
python -m unittest discover -s tests
```

## 10. Avaliação e entrega das respostas

O autor gera o texto e passa por validações automáticas. O Guardião revisa o texto
com a referência selecionada e retorna JSON. Erros factuais precisam citar trechos
reais da resposta e da base; incompletude precisa citar o pedido não atendido.
Uma reprovação fundamentada permite uma rodada de correção, seguida de nova
revisão. A barreira automática final permanece ativa mesmo com aprovação.

Fora da avaliação de exercícios, respostas sem aprovação são bloqueadas e dão
lugar a uma orientação segura. Na avaliação/esclarecimento, uma revisão
INCONCLUSIVA pode ser entregue se passar pelas verificações automáticas e não
houver falha técnica na correção. Isso fica registrado em
`revisao.entregue_sem_aprovacao`; não significa aprovação semântica.

Os três exercícios cadastrados possuem avaliadores em Python. Eles analisam as
tentativas acumuladas, indicam partes corretas, ajustes e a próxima pergunta.
O Inquiridor redige o feedback com esses fatos; o Guardião recebe os fatos, sem
o gabarito. Se o texto gerado for bloqueado, o fluxo usa o feedback do avaliador,
registrado com `revisao.resposta_verificada`. Esses avaliadores usam regras de
linguagem e podem não reconhecer formulações válidas: não são garantia geral
de correção semântica.

A memória salva o texto entregue e as decisões de revisão. Quando a avaliação
considera o exercício concluído, o turno recebe `exercicio_concluido` e a atividade
pode ser encerrada. Turnos bloqueados preservam o exercício pendente; exemplos
bloqueados não contam como mostrados. Pedidos de exercício e recusas não chamam
o modelo. Perguntas finais ficam restritas à prática.

Os documentos em `docs/superpowers/` registram propostas de implementação antigas;
o fluxo atual está descrito neste README e em [arquitetura](docs/arquitetura.md).
O relatório DOCX e o mini-relatório precisam de revisão da dupla antes da entrega,
inclusive das afirmações históricas sobre testes e resultados.
