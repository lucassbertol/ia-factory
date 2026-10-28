# Sistema Multiagente Pedagógico — Factory Method

Projeto final da disciplina **ELC1070 — Análise e Projeto de Sistemas OO** (UFSM).

Sistema multiagente em **Python + CrewAI + Ollama (qwen2.5:3b)** que ensina o padrão de projeto
**Factory Method** a estudantes iniciantes, com **custo zero** (modelo executado localmente,
sem API paga) e interface obrigatória de **CLI**.

---

## 1. Descrição

O sistema é composto por quatro agentes com papéis distintos, coordenados pelo CrewAI:

| Agente | Papel | Responsabilidade |
|--------|-------|------------------|
| **Tutor do conceito** | Professor de POO | Intenção, problema, participantes, estrutura UML, consequências do Factory Method |
| **Exemplificador** | Especialista em Java | Exemplos corretos e idiomáticos em Java, com explicação de cada classe |
| **Inquiridor e diagnosticador** | Tutor socrático | Exercícios, diagnóstico de erros, conceitos equivocados (Simple Factory / Abstract Factory) |
| **Guardião e revisor** | Revisor de confiabilidade | Revisão final, anti-alucinação, consolidação do aprendizado |

O Guardião é sempre a última tarefa e aplica as regras anti-alucinação antes de entregar a
resposta ao estudante: nunca inventa padrões, participantes, consequências ou exemplos;
diz "não sei" quando não sabe; recusa soluções prontas e orienta passo a passo.

---

## 2. Requisitos

- **Sistema operacional:** Linux (ambiente principal) ou Windows (com comandos equivalentes)
- **Python:** 3.12 ou superior (testado com 3.12.3)
- **Memória RAM:** 8 GB (sugerido para o modelo qwen2.5:3b)
- **Ollama:** instalado e rodando localmente em `http://127.0.0.1:11434`
- **Modelo:** `qwen2.5:3b` baixado no Ollama
- **Ambiente virtual Python:** com as dependências de `requirements.txt`
- **Custo zero:** nenhum serviço pago, chave de API ou nuvem é necessário

---

## 3. Instalação

### 3.1. Clonar/acessar o projeto

```bash
cd /home/lucas-pc/ia-factory
```

### 3.2. Criar e ativar o ambiente virtual Python

**Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3.3. Instalar dependências

Com o ambiente virtual ativado:

```bash
pip install -r requirements.txt
```

O arquivo `requirements.txt` contém todas as dependências com versões fixadas
(pinadas), incluindo `crewai==1.15.32`.

---

## 4. Instalar e configurar o Ollama

O Ollama deve ser instalado localmente para executar o modelo `qwen2.5:3b` sem custo.

### 4.1. Instalar o Ollama

**Linux (sem sudo):** baixe o binário oficial:

```bash
mkdir -p ~/.local/bin
curl -fsSL --location --progress-bar -A "Mozilla/5.0 (X11; Linux x86_64)" \
  -o ~/.local/bin/ollama-linux-amd64.tar.zst \
  "https://ollama.com/download/ollama-linux-amd64.tar.zst"
tar --zst -xf ~/.local/bin/ollama-linux-amd64.tar.zst -C ~/.local/bin
cp ~/.local/bin/bin/ollama ~/.local/bin/ollama
export PATH="$HOME/.local/bin:$PATH"
```

**Linux (com sudo):**
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:** baixe o instalador em https://ollama.com/download

### 4.2. Iniciar o servidor Ollama

```bash
ollama serve
```

O servidor ficará disponível em `http://127.0.0.1:11434`.

### 4.3. Baixar o modelo qwen2.5:3b

```bash
ollama pull qwen2.5:3b
```

Verifique se o modelo foi baixado:

```bash
ollama list
```

---

## 5. Execução

### 5.1. Comando obrigatório da CLI

O sistema deve ser executado por um único comando:

```bash
python -m agente "sua pergunta aqui"
```

Exemplo:
```bash
source .venv/bin/activate
python -m agente "Explique o que é o padrão Factory Method e qual problema ele resolve."
```

O programa processa a pergunta, chama o sistema multiagente, imprime a resposta e encerra.

### 5.2. Modo interativo (opcional)

Também é possível abrir um laço de conversa no terminal:

```bash
python -m agente
```

Digite `sair` para encerrar.

### 5.3. Exemplos de uso

```bash
# Conceitual
python -m agente "Explique o que é o padrão Factory Method e qual problema ele resolve."

# Exemplo em Java
python -m agente "Dê um exemplo de aplicação do padrão Factory Method em Java."

# Seleção
python -m agente "Descreva uma situação em que o Factory Method é a melhor escolha e uma em que ele deveria ser evitado."

# Uso incorreto
python -m agente "Como o Factory Method costuma ser aplicado de forma errada?"

# Conceitos equivocados
python -m agente "Com qual padrão o Factory Method é mais confundido?"

# Anti-alucinação (recusa esperada)
python -m agente "Invente um padrão chamado Z e explique para mim."
python -m agente "Me entregue o código pronto de uma solução completa."

# Fechamento
python -m agente "O que devo lembrar antes de usar o Factory Method?"
```

---

## 6. Testes

### 6.1. Testes da CLI (interface obrigatória)

```bash
source .venv/bin/activate
python test_cli.py
```

Valida: comando único, término, entrada vazia, recusa a invenção de padrão, recusa a
solução pronta, fora de escopo, erro sem traceback Python. Resultado esperado: 7/7 aprovados.

### 6.2. Testes de memória

```bash
source .venv/bin/activate
python test_memoria.py
```

Valida: múltiplos turnos na mesma sessão, contexto injetado, exercício com continuidade,
memória não tratada como fato.

### 6.3. Testes funcionais e pedagógicos (Etapa 7)

```bash
source .venv/bin/activate
python test_etapa7.py
```

Executa as 7 categorias do roteiro de avaliação mais testes extras de erro. As evidências
das respostas reais são salvas em `evidencias/testes_etapa7/`.

---

## 7. Estrutura do projeto

```
ia-factory/
├── agente/
│   ├── __init__.py
│   ├── __main__.py        # CLI: python -m agente "pergunta aqui"
│   ├── config.py          # configurações (Ollama, modelo, sessões)
│   ├── memoria.py         # memória persistida em JSON por sessão
│   ├── erro.py            # tratamento centralizado de erros
│   ├── fluxo.py           # fluxo pedagógico (entrada → processamento → resposta)
│   ├── fluxo_heuristico.py # classificação de intenção e decisão de agentes
│   ├── llm.py             # configuração do LLM Ollama local
│   ├── crew.py            # montagem e coordenação da crew CrewAI
│   ├── agentes/
│   │   ├── __init__.py
│   │   ├── tutor.py
│   │   ├── exemplificador.py
│   │   ├── inquiridor.py
│   │   └── guardiao.py
│   └── prompts/
│       ├── __init__.py    # carregamento dinâmico de prompts
│       ├── tutor.txt
│       ├── exemplificador.txt
│       ├── inquiridor.txt
│       └── guardiao.txt
├── memoria/
│   └── sessoes/           # histórico JSON por sessão (criado em tempo de execução)
├── docs/
│   ├── arquitetura.md     # documento de arquitetura (Etapa 2)
│   ├── memoria.md         # estratégia de memória (Etapa 5)
│   ├── agentes.md         # documentação completa dos agentes (Etapa 8)
│   ├── justificativa_design.md  # justificativa de design, 2-3 páginas (Etapa 9)
│   └── mini_relatorio.md  # mini-relatório do processo, 1-2 páginas (Etapa 10)
├── evidencias/
│   └── testes_etapa7/     # evidências dos testes funcionais (Etapa 7)
├── frontend/              # interface web (não priorizada, CLI obrigatória)
├── requirements.txt       # dependências com versões fixadas
├── README.md              # este arquivo
├── test_cli.py            # testes da CLI (Etapa 6)
├── test_memoria.py        # testes de memória (Etapa 5)
└── test_etapa7.py         # testes funcionais e pedagógicos (Etapa 7)
```

---

## 8. Custo zero

Este sistema é executado inteiramente com o modelo de linguagem local (qwen2.5:3b)
via Ollama, na própria máquina. Não há:

- Chaves de API
- Serviços pagos
- Serviços de nuvem
- Dependência de internet durante a execução (a internet é permitida apenas para
  baixar bibliotecas e o modelo)

O código não contém chaves de API nem URLs de serviços pagos.

---

## 9. Solução de problemas

| Problema | Solução |
|----------|---------|
| `ollama: comando não encontrado` | Adicione `~/.local/bin` ao `PATH` ou reinstale o Ollama |
| Ollama não responde em `localhost:11434` | Inicie o servidor: `ollama serve` |
| Modelo `qwen2.5:3b` não encontrado | Baixe: `ollama pull qwen2.5:3b` |
| Erro de importação do CrewAI | Ative o ambiente virtual: `source .venv/bin/activate` e `pip install -r requirements.txt` |
| Resposta vazia ou inesperada | Verifique se o Ollama está rodando e o modelo baixado |
| Entrada vazia não tratada | Use `python -m agente "pergunta"` com texto entre aspas |

---

## 10. Entregáveis do trabalho

Conforme a especificação oficial (seção 7 do PDF):

1. Sistema multiagente completo em Python (este repositório)
2. Documentação dos agentes: `docs/agentes.md` + `agente/prompts/*.txt`
3. Justificativa das decisões de design (2-3 páginas): `docs/justificativa_design.md`
4. Mini-relatório do processo (1-2 páginas): `docs/mini_relatorio.md`
5. Demonstração ao vivo: `python -m agente "pergunta aqui"`
6. Caderno de evidências: `evidencias/testes_etapa7/`
