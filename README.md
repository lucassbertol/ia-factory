# Sistema multiagente pedagógico — Factory Method

Projeto final de **ELC1070 — Análise e Projeto de Sistemas OO** (UFSM).

Quatro agentes de IA, coordenados pelo **CrewAI**, ensinam o padrão **Factory Method** a
estudantes iniciantes. Tudo roda na própria máquina com **Ollama + qwen2.5:3b**: sem chave de
API, sem nuvem, sem custo.

| Agente | Papel |
|---|---|
| **Tutor do conceito** | Intenção, problema, participantes, consequências, quando usar/evitar, comparações |
| **Exemplificador** | Explica exemplos Java **verificados** (compilados e executados pela dupla) |
| **Inquiridor** | Avalia as tentativas dos exercícios (banco verificado, com gabarito que não revela) e diagnostica equívocos |
| **Guardião** | Confere cada resposta contra a referência local e registra um veredito (APROVADO/REPROVADO) |

Pedidos para inventar padrões, nomes de padrões inexistentes, pedidos de solução pronta e
assuntos fora do escopo recebem uma recusa educada **sem chamar o modelo**, sempre com um
próximo passo. Detalhes: [arquitetura](docs/arquitetura.md), [agentes](docs/agentes.md),
[memória](docs/memoria.md).

---

## 1. Requisitos

- Python **3.12** (testado com 3.12.10 no Windows e 3.12.3 no Linux)
- **Ollama** instalado e aberto: https://ollama.com/download
- Modelo **qwen2.5:3b** (cerca de 2 GB); 8 GB de RAM bastam, 16 GB é o recomendado
- JDK (opcional), só para o teste que compila os exemplos Java

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

O `requirements.txt` tem as 138 dependências com versões fixas e marcadores por sistema
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
| `--limpar-sessao` | apaga a sessão indicada e encerra |
| `--nivel iniciante\|intermediario\|avancado` | ajusta a linguagem e o primeiro exemplo (também detectado em "sou iniciante") |
| `--silencioso` | não mostra o progresso nem o tempo (que vão para a saída de erro) |

Exemplo de prática com memória:

```bash
python -m agente --sessao ana "Proponha um exercício de Factory Method"
python -m agente --sessao ana "Minha resposta: Recibo seria o Product e ReciboPdf um ConcreteProduct"
python -m agente --sessao ana "Encerrar exercício"
```

Interface web opcional (a CLI continua sendo o ponto de entrada oficial):

```bash
python -m agente.web          # abra http://127.0.0.1:8000
```

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
| `MAX_REESCRITAS_GUARDIAO` | `0` | reescrita pedida pelo Guardião; desligada porque piorava as respostas nos testes reais |
| `AGENTE_DEBUG` | vazio | `1` mostra os logs internos do CrewAI |

A telemetria e o rastreamento do CrewAI são desligados em `agente/__init__.py`. O sistema roda
sem internet depois de instalado; para conferir, desligue a rede e execute uma pergunta.

## 5. Testes

```bash
python -m unittest -v tests.test_unitarios      # 40 testes, sem o modelo real (~20 s)
python tests/test_perguntas_pdf.py --extras     # roteiro + 6 casos-limite com o modelo real
```

Os testes unitários usam um Ollama simulado (`tests/ollama_simulado.py`) e cobrem o
roteamento (roteiro e 19 variações), as recusas, os guardrails, o veredito e a reescrita opcional do
Guardião, as falhas do Ollama, a memória, os prompts, a CLI e a compilação dos exemplos Java.
Eles **não** avaliam a qualidade das respostas do modelo: isso é feito lendo
`evidencias/respostas_teste.json`, gerado pelo segundo comando, cujo campo `julgamento` fica
para a dupla preencher.

## 6. Caderno de evidências (avaliação dos outros sistemas)

```bash
# formulário em branco para a sessão em sala
python caderno/avaliar_sistema.py --somente-formulario --padrao Strategy --dupla "Nome da dupla"
# ou rodando o roteiro direto no projeto da outra dupla
python caderno/avaliar_sistema.py --projeto "C:\caminho\do\projeto" --padrao Strategy --dupla "Nome da dupla"
```

Os formulários vão para `caderno/avaliacoes/`. Os critérios estão em
[caderno/rubrica.md](caderno/rubrica.md).

## 7. Estrutura

```text
agente/
  __main__.py          CLI (python -m agente)
  fluxo.py             orquestração de um turno
  fluxo_heuristico.py  roteador de intenções e barreiras anti-alucinação
  crew.py              agentes, tarefas e crews do CrewAI
  verificacao.py       guardrails determinísticos e leitura do veredito do Guardião
  llm.py               LLM local (Ollama /api/chat com num_ctx e temperatura)
  memoria.py           memória por sessão (JSON)
  recusas.py           recusas educadas e boas-vindas
  catalogo.py          nomes e intenções dos padrões GoF
  conhecimento.py      exemplos Java, fatos, UML e exercícios
  agentes/             leitura de ROLE/GOAL/BACKSTORY dos prompts
  prompts/             prompt de sistema de cada agente (fonte única)
  referencias/         referência conceitual e exemplos .java
  web.py               interface web opcional
tests/                 testes automáticos, simulador do Ollama, coleta do roteiro
caderno/               avaliação entre pares (script e rubrica)
docs/                  arquitetura, agentes, memória, justificativa, mini-relatório
frontend/              HTML/CSS/JS da interface web
```

## 8. Solução de problemas

| Problema | Solução |
|---|---|
| `[Erro] Não foi possível falar com o modelo local` | Abra o Ollama (no Windows, pelo menu Iniciar; no Linux, `ollama serve`) |
| `Modelo 'qwen2.5:3b' não encontrado` | `ollama pull qwen2.5:3b` |
| `ModuleNotFoundError: crewai` | Ative o `.venv` e rode `python -m pip install -r requirements.txt` |
| Acentos estranhos no terminal do Windows | Use o Windows Terminal ou rode `chcp 65001` antes |
| A primeira resposta demora muito | Normal: o modelo está sendo carregado na memória; as seguintes são mais rápidas |

## 9. Entregáveis

1. Sistema: este repositório (`requirements.txt`, `README.md`, código em `agente/`)
2. Documentação dos agentes: `docs/agentes.md` e seção 2 do relatório
3. Justificativa de design: `docs/justificativa_design.md` e seção 3 do relatório
4. Mini-relatório: `docs/mini_relatorio.md` e seção 4 do relatório
5. Demonstração ao vivo: `python -m agente`
6. Caderno de evidências: `caderno/avaliacoes/` (critérios em `caderno/rubrica.md`)
