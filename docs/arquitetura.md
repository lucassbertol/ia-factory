# Arquitetura do Sistema Multiagente Pedagógico — Factory Method

Projeto final da disciplina ELC1070 — Análise e Projeto de Sistemas OO (UFSM).

## 1. Visão geral

O sistema ensina o padrão de projeto **Factory Method** a estudantes iniciantes por meio de um conjunto de **quatro agentes com papéis distintos**, coordenados pelo **CrewAI**, executando localmente sobre o modelo **qwen2.5:3b** via **Ollama** (custo zero, sem API paga).

A interface obrigatória é uma **CLI de chat**:

```
python -m agente "pergunta aqui"
```

que processa o texto, chama o sistema multiagente, imprime a resposta e encerra. Há ainda um modo interativo contínuo (`sair` para encerrar).

## 2. Princípios de projeto

- **Simplicidade**: nenhuma abstração desnecessária; cada módulo tem uma única responsabilidade.
- **Baixo acoplamento**: os agentes não se conhecem diretamente; se coordenam apenas por meio da crew e do fluxo orquestrado.
- **Separação de responsabilidades**: cada agente tem papel pedagógico fixo (tutor, exemplificador, inquiridor/diagnosticador, guardião/revisor).
- **Custo zero**: execução 100% local com Ollama; sem chaves de API, sem serviços de nuvem, sem dependência de internet durante a execução.

## 3. Componentes

### 3.1 Pacote `agente/`

| Módulo | Responsabilidade |
|--------|------------------|
| `__main__.py` | Ponto de entrada da CLI (`python -m agente`). Analisa argumentos, trata entrada vazia, chama o fluxo e imprime a resposta. |
| `config.py` | Configurações centralizadas: URL do Ollama, nome do modelo (`qwen2.5:3b`), diretório de sessões, limites de tamanho. |
| `memoria.py` | Persistência e recuperação do histórico de conversa por sessão (arquivo JSON). Carrega/injeta o contexto anterior e salva novos turnos. |
| `erro.py` | Tratamento centralizado de erros: entrada vazia, falha do Ollama/modelo, saída inesperada, tempo esgotado. |
| `agentes/` | Definição dos quatro agentes pedagógicos (role, goal, backstory, escopo, regras). |
| `crew.py` | Montagem e coordenação da crew CrewAI: agentes, tarefas e dependências entre elas. |
| `fluxo.py` | Fluxo pedagógico: recebe a pergunta, decide a abordagem, executa os agentes, consolida a resposta final e atualiza a memória. |
| `prompts/` | Prompts de sistema completos de cada agente (arquivos `.txt`), carregados dinamicamente. |

### 3.2 Agentes (quatro papéis distintos)

| Agente | Papel | Responsabilidade pedagógica |
|--------|-------|-----------------------------|
| **Agente 1 — Tutor do conceito** | Professor de POO | Apresenta intenção, problema resolvido, participantes, estrutura UML e consequências do Factory Method. |
| **Agente 2 — Exemplificador** | Especialista em Java | Produz exemplos corretos e idiomáticos em Java, explica por que funcionam e adapta ao nível do estudante. |
| **Agente 3 — Inquiridor e diagnosticador** | Tutor socrático | Propõe exercícios, avalia respostas do estudante, detecta conceitos equivocados (ex.: Factory Method vs. Simple Factory / Abstract Factory) e orienta a correção. |
| **Agente 4 — Guardião e revisor** | Revisor de confiabilidade | Revisa a conversa e a resposta final, consolida o aprendizado, aponta lacunas e aplica as regras anti-alucinação (recusa a invenção de fatos e a entrega de solução pronta). |

### 3.3 Coordenação (CrewAI)

- **Processo**: sequencial com revisão final.
- **Orquestração**: o fluxo (`fluxo.py`) monta a crew dinamicamente conforme a intenção da pergunta do estudante (conceito, exemplo, exercício, diagnóstico, fechamento).
- **Dependências de tarefas**:
  1. Tutor apresenta o conceito quando a pergunta é conceitual.
  2. Exemplificador fornece o exemplo em Java quando solicitado.
  3. Inquiridor conduz o exercício e diagnostica a resposta do estudante.
  4. Guardião revisa sempre a resposta final antes de imprimi-la (última tarefa da sequência).
- **Evitar redundância**: o Guardião remove repetições e contradições entre agentes antes de consolidar.

## 4. Memória da conversa

- **Onde é armazenada**: arquivo JSON por sessão em `memoria/sessoes/<id_sessao>.json`.
- **O que é mantido**: histórico de turnos (pergunta do estudante, resposta do sistema, agente responsável, timestamp).
- **Como é usada**: a cada chamada CLI, o histórico da sessão é carregado e injetado como contexto nos prompts dos agentes, de modo que o diálogo permaneça coerente ao longo de vários turnos (ex.: o estudante responde a um exercício proposto anteriormente).
- **Memória ≠ conhecimento factual**: informações ditas pelo modelo anteriormente não são tratadas automaticamente como verdade; o Guardião reavalia a confiabilidade em cada turno.

## 5. Tratamento de erros

| Situação | Tratamento |
|----------|------------|
| Entrada vazia | Mensagem amigável pedindo uma pergunta válida; não chama o modelo. |
| Falha/indisponibilidade do Ollama | Mensagem compreensível informando que o modelo local não está acessível, com instrução para iniciar o Ollama. |
| Saída inesperada do modelo | O Guardião detecta e responde que não conseguiu gerar uma resposta confiável, sugerindo reformular a pergunta. |
| Pergunta fora do escopo (não Factory Method) | Resposta educada dizendo que o sistema ensina apenas o Factory Method e recomendando consulta ao material da disciplina. |
| Pedido de invenção de padrão ou solução pronta | Recusa educada, aplicando as regras anti-alucinação; orienta o estudante passo a passo em vez de entregar solução pronta. |

## 6. Fluxo entre entrada e resposta

```
Estudante digita pergunta
        │
        ▼
   Fluxo (fluxo.py)
        │
        ├─► Carrega memória da sessão (memoria.py)
        ├─► Classifica a intência da pergunta (conceito / exemplo / exercício / diagnóstico / fechamento)
        ├─► Monta a crew com os agentes relevantes (crew.py)
        ├─► Executa as tarefas CrewAI em sequência
        ├─► Guardião revisa e consolida a resposta final (anti-alucinação)
        ├─► Salva o turno na memória (memoria.py)
        └─► Imprime a resposta e encerra (ou aguarda próxima entrada no modo interativo)
```

## 7. Estrutura de diretórios

```
ia-factory/
├── agente/
│   ├── __init__.py
│   ├── __main__.py        # CLI ponto de entrada
│   ├── config.py          # configuracoes (Ollama, modelo, sessoes)
│   ├── memoria.py         # memoria persistida em JSON por sessao
│   ├── erro.py            # tratamento centralizado de erros
│   ├── fluxo.py           # fluxo pedagogico (entrada -> processamento -> resposta)
│   ├── crew.py            # montagem e coordenacao da crew CrewAI
│   ├── agentes/
│   │   ├── __init__.py
│   │   ├── tutor.py
│   │   ├── exemplificador.py
│   │   ├── inquiridor.py
│   │   └── guardiao.py
│   └── prompts/
│       ├── tutor.txt
│       ├── exemplificador.txt
│       ├── inquiridor.txt
│       └── guardiao.txt
├── memoria/
│   └── sessoes/           # historico JSON por sessao (criado em tempo de execucao)
├── docs/
│   └── arquitetura.md     # este documento
├── requirements.txt       # dependencias fixadas (etapa 1)
├── README.md              # (etapa 11)
└── ...                    # entregaveis posteriores (documentacao, relatorios, evidencias)
```

## 8. Critérios de aceitação da Etapa 2

- [x] Arquitetura documentada (este arquivo).
- [x] Responsabilidades distintas para os quatro agentes.
- [x] Coordenação definida (CrewAI, processo sequencial com revisão do Guardião).
- [x] Estratégia de memória definida (JSON por sessão, contexto injetado, memória != fato).
- [x] Estrutura de diretórios criada.
- [x] Nenhuma dependência de serviço pago.
