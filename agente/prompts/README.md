# Prompts do sistema dos agentes (Factory Method)

Estes arquivos contem o texto completo do prompt de sistema (persona/role,
objetivo/goal, contexto/backstory, escopo, estrategia pedaggica, regras
anti-alucinacao e formato das respostas) de cada agente.

Eles sao carregados dinamicamente pelo sistema e documentados na
Etapa 8.

Arquivos:
- tutor.txt — Agente 1: apresenta intencao, problema, participantes, estrutura UML e consequencias do Factory Method.
- exemplificador.txt — Agente 2: produz exemplos corretos e idiomaticos em Java.
- inquiridor.txt — Agente 3: propõe exercicios, avalia respostas, diagnostica conceitos equivocados de forma socratica.
- guardiao.txt — Agente 4: revisa a conversa, consolida o aprendizado, aplica regras anti-alucinacao.

Cada prompt segue o esqueleto do Anexo B da especificacao oficial:
  ROLE / GOAL / BACKSTORY / ESCOPO / ESTRATEGIA PEDAGOGICA /
  EXEMPLOS / CASOS DE ERRO / REGRAS ANTI-ALUCINACAO / FORMATO DAS RESPOSTAS

Conteudo implementado na Etapa 3.

Apos cada prompt, `crew.py` anexa a referencia local de
`agente/referencias/factory_method.md`, carregada por `agente/conhecimento.py`.
Nas tarefas de exemplo, Exemplificador e Guardiao recebem tambem os exemplos
Java locais. Nao ha consultas de rede nem compilacao de codigo do estudante
durante a conversa. Consulte `docs/revisao_conceitual.md` para a revisao e seus
limites. Alteracoes nos `.txt` devem ser refletidas em `docs/agentes.md`.
