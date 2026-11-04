# Guardião bloqueante Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Impedir entrega de respostas sem aprovação e limitar a correção a uma rodada.
**Architecture:** Parser JSON com validação de evidências em verificacao.py; crews de reescrita e revisão explícitas; decisão e memória em fluxo.py.
**Tech Stack:** Python 3.12, unittest e CrewAI existentes.
**Spec:** docs/superpowers/specs/2026-11-04-guardiao-bloqueante-design.md

## Global Constraints
- Não alterar a fonte unificada nem enviar gabaritos a novos destinatários.
- No máximo uma rodada de correção; sempre revisar a versão corrigida.
- JSON inválido, evidência ausente e veredito inconclusivo nunca liberam texto.
- Manter respostas determinísticas de exercícios/recusas.

## Review Focus
- Aprovação contraditória ou JSON truncado: saída segura.
- Autores múltiplos: corrigir os afetados e revisar todo o conjunto.
- Persistência: rascunho reprovado não vira resposta/histórico pedagógico.
- Falha técnica na correção/revisão: saída segura sem nova tentativa.
- Reescrita não permite retry adicional de guardrail nem loop por configuração.

### Task 1: Contrato e validação
- [x] Testar JSON válido/inválido, citações e incompletude; observar falha.
- [x] Implementar avaliar_revisao e substituir o contrato do Guardião.

### Task 2: Fluxo e integração
- [x] Testar aprovação, correção+aprovação, rejeição persistente, inconclusivo,
  falha técnica, evidência inventada, múltiplos autores e memória.
- [x] Implementar revisão final explícita e bloqueio de entrega.
- [x] Atualizar configuração, prompts e documentação.
- [x] Executar suíte sem Ollama, compileall e diff --check; revisão independente.

Execução na pasta atual: criação de branch já bloqueada pelo ambiente na tarefa
anterior. Não criar commits nem publicar nesta tarefa.

## Resultado

27 testes passaram com `python -m unittest discover -s tests` (sem Ollama).
`compileall -q agente` e `git diff --check` passaram. CrewAI emitiu avisos de
depreciação próprios. Revisão independente identificou P2 de estado pedagógico:
fechamento bloqueado apagava exercício e conceito bloqueado contava como
estudado. Duas regressões falharam antes da correção em memoria.py e passaram
depois; revisor confirmou a correção. Sem commits/publicação. Ainda não há
avaliação de qualidade/latência do novo contrato com o modelo real.
