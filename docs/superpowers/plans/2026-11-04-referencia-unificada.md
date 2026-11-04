# Referência unificada Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Usar um único Markdown como fonte do material didático.
**Architecture:** Parser de seções identificadas e validação dos campos; manter as interfaces de seleção existentes. Referência conceitual selecionada por intenção, sem incluir gabaritos nos prompts compartilhados.
**Tech Stack:** Python 3.12, unittest, CrewAI existente; sem novas dependências.
**Spec:** docs/superpowers/specs/2026-11-04-referencia-unificada-design.md

## Global Constraints
- Preservar códigos, saídas, exercícios e identificadores atuais.
- Não chamar Ollama na verificação automática.
- Gabaritos só na avaliação/esclarecimento do Inquiridor.

## Review Focus
- Seção ausente, vazia ou duplicada gera erro claro.
- Cercas de código não criam seções falsas.
- Seleção por intenção não inclui gabaritos.
- Agentes e Guardião recebem referência e fatos consistentes.
- Sessões existentes continuam reconhecendo os identificadores dos exercícios.

### Task 1: Fonte unificada e leitura
- [x] Criar testes unittest para leitura, seleção, conteúdo e erros do Markdown; observar falha.
- [x] Migrar o conteúdo integral sem reescrever Java e exercícios.
- [x] Implementar parser e adaptar conhecimento.py preservando interfaces.
- [x] Executar testes de conhecimento.

### Task 2: Integração e documentação
- [x] Testar prompts reais sem rede: seleção por intenção, fatos ao Guardião e isolamento de gabaritos.
- [x] Adaptar crew.py para seleção e contexto de revisão.
- [x] Remover fontes redundantes e atualizar documentação de uso.
- [x] Executar unittest discovery, compilação/execução Java em pasta temporária e revisão do diff.

Execução local autorizada pelo pedido de implementação do desenho sugerido.
Não criar commits nem publicar alterações nesta tarefa.

## Resultado

Implementação e revisão independente concluídas. 8 testes passaram com
`python -m unittest discover -s tests`; `compileall` e `git diff --check` passaram.
Comparação com snapshot anterior confirmou preservação integral dos códigos,
saídas, apresentação, fatos, UML e exercícios/gabaritos. Sem chamadas ao Ollama.
Java não recompilado: `javac` ausente. CrewAI emitiu avisos de depreciação próprios.
A criação da branch foi bloqueada pelo ambiente; alterações ficaram na pasta
atual, sem commit. O PDF não rastreado preexistente foi preservado.
