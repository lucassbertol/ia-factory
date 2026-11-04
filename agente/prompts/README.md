# Prompts de sistema dos agentes

Fonte única das instruções de cada agente. Cada arquivo segue o esqueleto do Anexo B da
especificação: ROLE, GOAL, BACKSTORY, ESCOPO, ESTRATÉGIA PEDAGÓGICA, EXEMPLOS, CASOS DE ERRO,
REGRAS ANTI-ALUCINAÇÃO e FORMATO DAS RESPOSTAS.

| Arquivo | Agente | Papel no turno |
|---|---|---|
| `tutor.txt` | Tutor do conceito | autor: conceito, seleção, comparação, fechamento |
| `exemplificador.txt` | Exemplificador | autor: explica exemplos Java verificados e o uso incorreto |
| `inquiridor.txt` | Inquiridor | autor: exercícios, avaliação de tentativas, diagnóstico |
| `guardiao.txt` | Guardião | verificador: devolve VEREDITO (APROVADO/REPROVADO + problemas) |

Como são usados:

- `agente/agentes/__init__.py` lê ROLE, GOAL e BACKSTORY, que o CrewAI recebe em campos próprios;
  as demais seções vão junto com o backstory.
- `agente/crew.py` anexa ao backstory a referência `agente/referencias/factory_method.md` e
  monta a descrição da tarefa do turno (pergunta, nível, histórico, contrato da intenção e
  material verificado).
- `tests/test_unitarios.py` confere que os quatro arquivos têm todas as seções do Anexo B.

Ao alterar um prompt, regenere a documentação (`docs/agentes.md` e a seção 2 do relatório),
que reproduz o texto integral.
