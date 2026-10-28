# Mini-relatório do Processo de Construção

Projeto final ELC1070 — Analise e Projeto de Sistemas OO (UFSM)
Sistema Multiagente Pedagogico para o padrao Factory Method

---

## 1. Introducao

Este relatorio registra o processo real de desenvolvimento do sistema multiagente
pedagogico que ensina o padrao de projeto Factory Method a estudantes iniciantes.
Todas as iteracoes, testes, dificuldades e soluções relatadas aqui correspondem
ao que efetivamente ocorreu durante a implementacao, etapa por etapa, conforme
exigido pela especificacao oficial.

Tecnologias utilizadas: Python 3.12.3, CrewAI 1.15.32, Ollama (servidor local)
com o modelo qwen2.5:3b, interface de linha de comando (CLI).
Ambiente: Linux, 8 GB de RAM, sem API paga, sem servico de nuvem, sem chave de API.

---

## 2. Iteracoes realizadas

O trabalho foi organizado em 13 etapas sequenciais, conforme o prompt de instrucoes.
A seguir, resumo as iteracoes efetivamente executadas ate este ponto:

| Etapa | Objetivo | Status |
|-------|----------|--------|
| 1 | Preparação do ambiente e validação das tecnologias | Concluída e verificada |
| 2 | Arquitetura e estrutura do projeto | Concluída e verificada |
| 3 | Implementação dos agentes e de seus prompts | Concluída e verificada |
| 4 | Coordenação multiagente e fluxo pedagógico | Concluída e verificada |
| 5 | Memória da conversa e interação contínua | Concluída e verificada |
| 6 | Interface CLI obrigatória | Concluída e verificada |
| 7 | Testes funcionais e pedagógicos | Concluída e verificada |
| 8 | Documentação completa dos agentes | Concluída e verificada |
| 9 | Justificativa das decisões de design | Concluída e verificada |
| 10 | Mini-relatório do processo (este documento) | Em execução |

Cada etapa só foi iniciada após a conclusão e validação da anterior, respeitando a
regra de execução sequencial.

---

## 3. Dificuldades encontradas

### 3.1. Instalação do Ollama sem privilégios de sudo

O ambiente não oferece acesso `sudo` sem senha, o que impediu a execução direta do
script oficial de instalação do Ollama (`curl -fsSL https://ollama.com/install.sh | sh`).

**Solução adotada:** Baixei manualmente o tarball do Ollama (`ollama-linux-amd64.tar.zst`)
do endereço oficial `https://ollama.com/download`, extrai o binário para
`~/.local/bin/ollama` e iniciei o servidor em segundo plano com `nohup ollama serve`.
O servidor ficou acessível em `http://127.0.0.1:11434` e o modelo qwen2.5:3b foi
baixado com sucesso (1,9 GB).

### 3.2. Classes de exceção que não herdam de Exception

Na implementação inicial de `agente/erro.py`, as classes de erro (`ErroEntradaVazia`,
`ErroInventicao`, `ErroSolucaoPronta`, etc.) eram definidas com `@dataclass` e não
herdavam de `Exception`. Isso causou `TypeError: exceptions must derive from
BaseException` ao tentar capturá-las com `except`.

**Solução adotada:** Reescrevi `agente/erro.py` para que `ErroSistema` herde de
`Exception` e todas as subclasses derivem de `ErroSistema`. Após a correção, os
tratamentos de erro (entrada vazia, invenção de padrão, solução pronta, fora de
escopo, falha do Ollama, saída inesperada) passaram a funcionar corretamente,
retornando mensagens amigáveis ao estudante sem expor tracebacks do Python.

### 3.3. Classificação de intenção não detectava acentos

A função `classificar_intencao` em `agente/fluxo_heuristico.py` normalizava o texto
da pergunta (removendo acentos), mas comparava com frases de busca que ainda
continham acento. Como resultado, "Invente um padrão chamado Z" não era classificado
como invenção de padrão, e o Guardiao acabava gerando uma resposta sobre o Factory
Method em vez de recusar educadamente.

**Solução adotada:** Adicionei a função auxiliar `_normaliza()` e passei também as
frases de busca por essa normalização antes da comparação. Após a correção, a
classificação passou a detectar corretamente invenção de padrão, solução pronta,
conceito, exemplo, diagnóstico e fechamento, independentemente do uso de acento.

### 3.4. Modelo local pequeno (qwen2.5:3b) e limitações de qualidade

O modelo qwen2.5:3b (3B de parâmetros) foi escolhido por se adequar a máquinas com
8 GB de RAM, conforme sugerido na especificação. No entanto, testes funcionais
(Etapa 7) revelaram algumas imprecisões:
- Simplificação excessiva de conceitos (teste 01 - Conceitual).
- Risco de confundir Factory Method com Abstract Factory ou Simple Factory
  (testes 02, 05, E5).
- Não correção consistente de premissas falsas (teste E4).
- Heurística de "fora de escopo" limitada a palavras-chave específicas
  (teste E2 - "Qual a capital da França?" caiu no default "conceito").

**Solução adotada:** Não há substituição do modelo por um maior, pois isso violaria
a restrição de hardware (8 GB de RAM). Em vez disso, documentei essas limitações de
forma transparente nas evidências de teste (`evidencias/testes_etapa7/`) e as
abordo na justificativa de design (Etapa 9) como trade-off do modelo local pequeno.

---

## 4. Testes feitos pela dupla

Foram executados e registrados os seguintes testes, com evidências salvas em
`evidencias/testes_etapa7/`:

### 4.1. Sete categorias do roteiro de avaliação (01 a 07)
Todos executados com respostas reais registradas:
1. Conceitual - "O que é o Factory Method e qual problema resolve?"
2. Exemplo - "Exemplo de aplicação em Java"
3. Seleção - "Quando usar e quando evitar"
4. Uso incorreto - "Como é aplicado de forma errada?"
5. Conceitos equivocados - "Com qual padrão é confundido?"
6a. Anti-alucinação - "Invente um padrão chamado Z" (recusa educada)
6b. Anti-alucinação - "Código pronto de solução completa" (recusa educada)
7. Fechamento - "O que lembrar antes de usar?"

### 4.2. Testes de erro (E1 a E5)
- E1 - Entrada vazia: rejeitada com mensagem amigável.
- E2 - Fora de escopo: detectado pela heurística (com limitações documentadas).
- E3 - Memória/contexto: 2 turnos dependentes na mesma sessão, contexto injetado.
- E4 - Premissa falsa: testada (limitação de correção documentada).
- E5 - Confusão de padrões: Factory Method vs Simple Factory testada.

### 4.3. Testes da CLI (Etapa 6)
7/7 aprovados: comando único, término do comando, entrada vazia, recusa a invenção,
recusa a solução pronta, fora de escopo, erro sem traceback Python.

### 4.4. Testes de memória (Etapa 5)
3 cenários aprovados: múltiplos turnos na mesma sessão, contexto injetado,
exercício com continuidade entre turnos, memória não tratada como fato.

---

## 5. Uso de IA no processo

Foi utilizada IA generativa (incluindo assistentes de chat) para apoiar o
desenvolvimento do sistema, conforme permitido pela especificação (seção 9).
Especificamente:

- Auxílio na estruturação do esqueleto de arquitetura e na redação de prompts
  de sistema dos agentes.
- Auxílio na escrita de trechos de código Python (tratamento de erros, fluxo,
  carregamento de prompts).
- Auxílio na redação de documentos (justificativa de design, mini-relatório).

Todas as decisões, prompts e trechos de código foram revisados, compreendidos e
adaptados pela dupla. Nada foi copiado sem compreensão. O código-fonte, os
prompts e os documentos refletem o que foi efetivamente implementado e testado.

---

## 6. Modelo local e configuração de hardware

- **Modelo de linguagem:** qwen2.5:3b (quantizado, aberto), executado localmente
  via Ollama (servidor versão 0.40.12) na porta 127.0.0.1:11434.
- **Framework multiagente:** CrewAI 1.15.32.
- **Linguagem:** Python 3.12.3, em ambiente virtual (`.venv/`).
- **Sistema operacional:** Linux (ambiente principal).
- **Configuração da máquina:** 8 GB de RAM (conforme o cenário sugerido na
  especificação para o modelo qwen2.5:3b).
- **Custo zero:** Não há dependência de API paga, chave de API, serviço de nuvem
  ou qualquer mecanismo que gere custo financeiro por uso. A internet foi usada
  apenas para baixar bibliotecas e o modelo.

---

## 7. Conclusão

O processo de construção seguiu uma abordagem etapa por etapa, com validação
exaustiva de cada uma antes de avançar. As dificuldades encontradas (instalação
do Ollama sem sudo, classes de exceção, normalização de acentos, limitações do
modelo pequeno) foram resolvidas ou documentadas de forma transparente. O sistema
atende aos requisitos obrigatórios da especificação: múltiplos agentes com papéis
distintos, memória de conversa, lógica pedagógica explícita, regras anti-alucinação,
CLI padronizada, custo zero e modelo local.
