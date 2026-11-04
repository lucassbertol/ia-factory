# Testes

## Com o modelo real (roteiro da avaliação)

Com o Ollama aberto e o `qwen2.5:3b` baixado:

```bash
python tests/test_perguntas_pdf.py            # 8 perguntas do roteiro
python tests/test_perguntas_pdf.py --extras   # + 6 casos-limite
```

Cada pergunta usa uma sessão nova. O resultado vai para `evidencias/respostas_teste.json`
(substituído a cada execução; copie antes se quiser guardar), com resposta integral,
intenção, agentes, veredito do Guardião, duração e um campo `julgamento` para a dupla
preencher. Os estados são `respondida` (modelo), `recusa` (resposta determinística),
`erro` e `interrompida`. Código de saída 0 indica coleta concluída, 1 erro, 130 interrupção.

## Referência unificada (sem modelo)

`python -m unittest discover -s tests` verifica leitura do Markdown, seleção de
conceitos, preservação do material e isolamento dos gabaritos nos prompts reais.
A construção das crews usa armazenamento temporário; não executa `kickoff` nem
chama o Ollama. O coletor do roteiro só roda quando invocado explicitamente.

A suíte também testa a decisão bloqueante do Guardião: JSON e evidências,
correção única, revisão final, orientação segura, falhas e memória. Usa saídas
controladas na fronteira da execução das crews; não chama o Ollama.
