# Mini-relatório do processo de construção

Versão em Markdown da seção 4 do relatório de entrega.

## 4.1. Iterações e testes

| Iteração | Alteração ou objetivo | Teste/evidência e resultado |
|---|---|---|
| 1 | Estrutura inicial (até 28/10): quatro agentes do Anexo A, todos executados em sequência, prompts em .txt. | As primeiras execuções mostraram que a pergunta do estudante não chegava às tarefas: quase tudo virava explicação do Tutor. Passamos a injetar pergunta, contexto e intenção em todas as tarefas (teste de roteamento). |
| 2 | Memória em JSON por sessão, exercício em andamento e CLI com --sessao. | Testes da CLI: comando único, entrada vazia, recusas, modelo indisponível e sessão inválida, sem traceback. |
| 3 | Roteiro completo com o modelo (28/10, evidencias/testes_etapa7). | Respostas com erros: o cenário 05 respondeu com um exercício em C#; o E5 descreveu errado o Simple Factory; o exemplo tinha várias classes public em um arquivo. |
| 4 | Roteamento refinado (03/11): intenções de seleção, comparação, uso incorreto e esclarecimento; contexto só quando necessário; interface web. | Execução completa de 03/11 (evidencias/execucoes): o Java gerado no cenário 02 não compilou com javac; UML ilegível no cenário 01; o cenário 05 disse 'confundido com o Factory Method'. |
| 5 | Revisão de engenharia (03/11): LLM próprio com num_ctx e temperatura; exemplos verificados; Guardião verificador; guardrails; barreiras anti-alucinação; requirements para Windows e Linux. | 27 testes automáticos com Ollama simulado passando; requisições conferidas (num_ctx 8192, temperatura 0.2); os quatro exemplos Java compilados e executados. |
| 6 | Primeira coleta com o modelo real após a revisão (04/11): tests/test_perguntas_pdf.py --extras, 14 perguntas. | As 6 recusas foram corretas; média de 19 s por resposta. Mas o Guardião reprovou as 8 respostas com problemas inventados, e as reescritas copiaram falsidades ('o Factory Method não é GoF'); o E3 aceitou a premissa falsa; o E4 entrou em laço de frases; apareceram ecos da pergunta e frases cortadas. |
| 7 | Correções a partir da coleta: problema do Guardião só vale com trecho citado; reescrita só substitui se não piorar; detecção de premissa falsa na pergunta; remoção de laços, frases cortadas e texto de bastidor; repeat_penalty 1.15. | Segunda coleta (04/11): nenhuma falsidade grave nas respostas finais; E3 passou a corrigir a premissa falsa; E4 sem laço; 14 de 20 problemas do Guardião descartados por não citarem trecho real; tempo médio caiu de 19 s para 12 s. |
| 8 | Ajustes finos da segunda coleta: problema do Guardião precisa também explicar o erro (não basta citar) e não pode copiar o exemplo do prompt; remoção de frases que comentam a própria resposta; fechamento sem copiar a referência. | Terceira coleta (04/11): recusas corretas; mas as 6 reescritas pedidas pelo Guardião não corrigiram nenhum erro real e 4 pioraram a resposta ('Desculpe pela confusão anterior', uma resposta de 46 s); média de 17 s. |
| 9 | Decisão a partir das três coletas: reescrita pedida pelo Guardião desligada por padrão (veredito apenas registrado); remoção mecânica de frases com erro factual conhecido; mais padrões de texto de bastidor removidos. | Quarta coleta (04/11): nenhuma resposta piorada; tempo médio de 10 s; quase nenhum texto de bastidor. Restaram erros de conteúdo quando o modelo cria algo novo: no exercício (E5) trocou PDF com CSV e entregou a solução; no exemplo (02) disse que Email e Sms criam objetos; no uso incorreto (04) localizou o erro na classe errada; na comparação (E4) disse que Strategy usa sobrescrita. |
| 10 | Banco de exercícios verificados (enunciado + gabarito) e avaliação das tentativas pelo Inquiridor contra o gabarito, sem revelá-lo; fatos verificados de cada exemplo entregues ao Exemplificador; intenções de Strategy e State corrigidas (composição); novas regras para os erros da quarta coleta. | 39 testes automáticos, 10 com saídas reais das coletas. [Quinta coleta e julgamento da dupla — completar]. |

## 4.2. Dificuldades identificadas e soluções

| Dificuldade | Como foi identificada | Solução adotada / situação final |
|---|---|---|
| Modelo local lento | Tempo de cada pergunta com os quatro agentes em sequência. | Um autor por turno mais o Guardião (veredito curto), num_predict 800, repeat_penalty 1.15 e recusas sem modelo. Primeira coleta de 04/11: 19 s por resposta; segunda, depois dos ajustes: 12 s. |
| Agente fora do papel | Comparação respondida com exercício; o Guardião substituía o exemplo por uma explicação genérica. | Contratos por intenção na descrição da tarefa; o Guardião passou a dar veredito em vez de reescrever. |
| Erros conceituais e código errado do modelo de 3B | Leitura das evidências e compilação do Java gerado com javac. | Exemplos Java verificados, guardrails com os erros observados, referência local revisada e janela de contexto de 8192 tokens. |
| Guardião inventando problemas | Coleta real de 04/11: 8 de 8 respostas reprovadas sem motivo real; a reescrita piorava o texto. | Exigência de trecho citado e explicação; depois de três coletas sem nenhuma reescrita útil, a reescrita foi desligada por padrão e o veredito passou a ser só registrado. |
| Prompt cortado em silêncio | Investigação do CrewAI 1.15: o endpoint compatível com a OpenAI não envia num_ctx. | LLM próprio (BaseLLM) chamando /api/chat com num_ctx, temperatura e limite de tokens. |
| Instalação no Windows | O .venv do Windows estava incompleto (sem crewai): o requirements gerado no Linux trazia uvloop, que não existe para Windows. | requirements.txt gerado com marcadores por sistema (uv pip compile --universal) e conferido para Windows e Linux. |
| Telemetria e pergunta de 'traces' do CrewAI | Leitura do código do framework: ele tenta enviar dados e, na primeira execução, faz uma pergunta no terminal. | Variáveis de ambiente definidas antes do import e recusa registrada nas preferências locais. |
| Instalação do Ollama sem sudo (Linux) | O script oficial exigia sudo. | Binário oficial extraído em ~/.local/bin. |

## 4.3. Transparência do uso de IA no desenvolvimento

Ferramentas de IA usadas pela dupla durante o desenvolvimento: [completar: quais assistentes ou agentes de código foram usados nas etapas iniciais (estrutura, prompts, código, documentação), para quê e como os resultados foram verificados].

Em 03/11/2026 usamos o **Claude (Anthropic)** em uma sessão de agente com acesso à pasta do projeto para: revisar o sistema contra a especificação; investigar o CrewAI (descoberta da janela de contexto e da telemetria); implementar o LLM próprio, os guardrails, as barreiras anti-alucinação e os exemplos verificados; reescrever os prompts; criar os testes automáticos, o simulador do Ollama e o script do caderno de evidências; e redigir uma primeira versão das seções 3 e 4 deste relatório.

Verificação: lemos e discutimos cada mudança de código, rodamos os testes automáticos e o roteiro com o modelo real, compilamos os exemplos Java e revisamos e reescrevemos o texto deste relatório com as nossas palavras. [completar: o que a dupla alterou ou rejeitou do que foi sugerido].

O modelo incorporado ao tutor (qwen2.5:3b, local) é diferente das ferramentas de IA usadas para construir o projeto.

## 4.4. Modelo local e condições de execução

- **Modelo:** qwen2.5:3b (tag do Ollama), modelo aberto quantizado, executado localmente; nenhuma chave, nuvem ou serviço pago.
- **Servidor:** Ollama [versão — completar com `ollama --version`] em http://127.0.0.1:11434; o código usa só a API local `/api/chat`.
- **Parâmetros por chamada:** num_ctx 8192, temperature 0.2, num_predict 800, repeat_penalty 1.15, timeout de 180 s (ajustáveis por variáveis de ambiente em `agente/config.py`).
- **Máquina da demonstração:** Windows [versão — completar], [CPU — completar], 16 GB de RAM, [GPU — completar ou 'sem GPU'], Python 3.12.10.
- **Limitações observadas (coletas de 04/11):** média de 10 s por resposta na quarta coleta (de 4 a 26 s); o modelo de 3B tende a repetir frases, ecoar a pergunta e, como revisor, apontar problemas que não existem. Os filtros determinísticos contêm esses efeitos, mas não os eliminam.
