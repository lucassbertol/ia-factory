# Testes

## Sem o modelo real (rápido)

```bash
python -m unittest -v tests.test_unitarios
```

40 testes que usam um Ollama simulado (`ollama_simulado.py`): ele devolve respostas
roteirizadas por agente e registra cada requisição. Cobrem roteamento e barreiras
anti-alucinação, recusas, guardrails, veredito do Guardião e reescrita opcional, parâmetros enviados ao
Ollama (num_ctx, temperatura), falhas do Ollama, memória, prompts (seções do Anexo B), CLI e os
exemplos Java (compilados e executados quando há `javac`). A memória dos testes vai para uma
pasta temporária: as suas sessões não são tocadas.

Esses testes **não** avaliam a qualidade das respostas do modelo.

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
