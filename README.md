# Sistema multiagente pedagógico — Factory Method

Trabalho de **ELC1070 — Análise e Projeto de Sistemas OO** (UFSM). O tutor usa quatro agentes do CrewAI e o modelo local `qwen2.5:3b` para ensinar Factory Method. A interface principal é o terminal. O projeto também oferece um chat no navegador.

## 1. Instalar os pré-requisitos

- **Python 3.12**. No Linux, a instalação precisa incluir o módulo `venv`.
- **Ollama**. Siga o guia para [Linux](https://docs.ollama.com/linux) ou [Windows](https://docs.ollama.com/windows).
- **Espaço em disco** para o Ollama, as dependências e o modelo de aproximadamente 2 GB. [Modelo qwen2.5:3b](https://ollama.com/library/qwen2.5:3b)

Baixe ou clone o projeto, extraia o ZIP se for o caso e abra um terminal na pasta que contém este README e o `requirements.txt`. Execute os comandos do projeto a partir dessa pasta.

## 2. Preparar o ambiente

### Linux (Bash)

```bash
python3.12 --version
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Rode `ollama list` para verificar se o Ollama está ativo. Se o comando indicar que o servidor está inacessível, rode `ollama serve` em outro terminal e deixe-o aberto durante o uso. Se instalou o Ollama como serviço, pode iniciá-lo com `sudo systemctl start ollama`.

### Windows (PowerShell)

```powershell
py -3.12 --version
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Se `py` estiver indisponível, rode `python --version`. Caso o comando mostre Python 3.12, use `python -m venv .venv`.

Abra o Ollama pelo menu Iniciar caso ele ainda não esteja em execução. Se acabou de instalar, abra um novo PowerShell para que o comando `ollama` fique disponível.

Se o PowerShell bloquear a ativação, rode `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` e tente ativar novamente. Essa configuração vale apenas para o terminal atual.

Sempre que abrir outro terminal para executar o projeto, volte à pasta do README e repita o comando de ativação do seu sistema.

### Baixar o modelo (Linux e Windows)

Com o Ollama ativo, rode:

```text
ollama pull qwen2.5:3b
ollama list
```

Confira se `qwen2.5:3b` aparece na lista. O download das dependências e do modelo exige internet. Depois da instalação, o tutor roda localmente.

## 3. Executar pelo terminal

A pergunta abaixo imprime uma resposta e encerra o programa. Execute o comando sem a pergunta para abrir o modo interativo. Digite `sair` para encerrar.

```text
python -m agente "Explique o que é o padrão Factory Method e qual problema ele resolve."
python -m agente
```

Use `--sessao ID` para retomar a mesma conversa em outra execução. Por exemplo, acrescente `--sessao pratica` antes de `"Proponha um exercício de Factory Method"` e repita o mesmo identificador ao enviar sua tentativa. Para apagar essa sessão, execute o módulo com `--sessao pratica --limpar-sessao`. Use `python -m agente --help` para consultar todas as opções.

## 4. Executar no navegador (opcional)

```text
python -m agente.web
```

Deixe o terminal aberto e acesse [o chat em http://127.0.0.1:8000](http://127.0.0.1:8000). Se a porta estiver ocupada, acrescente `--port 8001` ao comando e abra [http://127.0.0.1:8001](http://127.0.0.1:8001). Para encerrar o servidor web, pressione `Ctrl+C` no terminal.

## 5. Executar os testes

O primeiro comando roda os testes automatizados locais. O segundo envia as oito perguntas do roteiro de avaliação ao modelo e precisa do Ollama ativo.

```text
python -m unittest discover -s tests
python tests/test_perguntas_pdf.py
```

O coletor grava as respostas completas em `evidencias/respostas_teste.json` e substitui o arquivo a cada execução. A avaliação pedagógica é feita pela dupla após ler as respostas. Acrescente `--extras` ao segundo comando para incluir seis casos adicionais. Consulte [o guia de testes](tests/README.md).

## Solução de problemas

| Problema | O que fazer |
|---|---|
| Python 3.12 indisponível | Instale essa versão. No Linux, confirme que `python3.12` está no caminho do terminal. No Windows, abra um novo PowerShell após instalar. |
| Erro ao criar o ambiente no Linux | Instale o suporte a `venv` para o Python 3.12. No Ubuntu 24.04 e no Linux Mint 22, o pacote é `python3.12-venv`. |
| `ModuleNotFoundError: crewai` | Ative a `.venv` e rode `python -m pip install -r requirements.txt`. |
| Falha na conexão com o modelo | Rode `ollama list`. Se o servidor estiver inacessível, inicie o Ollama conforme as instruções do seu sistema na etapa 2. |
| Modelo ausente | Com o Ollama ativo, rode `ollama pull qwen2.5:3b`. |

## Documentação do projeto

- [Arquitetura e fluxo de revisão](docs/arquitetura.md)
- [Agentes e prompts](docs/agentes.md)
- [Memória de conversa](docs/memoria.md)
- [Justificativa de design](docs/justificativa_design.md)
- [Mini-relatório](docs/mini_relatorio.md)
- [Referência didática com exemplos Java e exercícios](agente/referencias/factory_method.md)
- [Configurações do modelo e do fluxo](agente/config.py)
