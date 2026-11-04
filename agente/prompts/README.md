# Prompts de sistema dos agentes

Fonte única das instruções de cada agente. Cada arquivo segue o esqueleto do Anexo B da
especificação: ROLE, GOAL, BACKSTORY, ESCOPO, ESTRATÉGIA PEDAGÓGICA, EXEMPLOS, CASOS DE ERRO,
REGRAS ANTI-ALUCINAÇÃO e FORMATO DAS RESPOSTAS.

| Arquivo | Agente | Papel no turno |
|---|---|---|
| `tutor.txt` | Tutor do conceito | autor: conceito, seleção, comparação, fechamento |
| `exemplificador.txt` | Exemplificador | autor: explica exemplos Java verificados e o uso incorreto |
| `inquiridor.txt` | Inquiridor | autor: exercícios, avaliação de tentativas, diagnóstico |
| `guardiao.txt` | Guardião | verificador: devolve JSON (APROVADO/REPROVADO/INCONCLUSIVO) |

Como são usados:

- `agente/agentes/__init__.py` lê ROLE, GOAL e BACKSTORY, que o CrewAI recebe em campos próprios;
  as demais seções vão junto com o backstory.
- `agente/crew.py` anexa ao backstory as seções conceituais selecionadas de `agente/referencias/factory_method.md`, sem gabaritos, e
  monta a descrição da tarefa do turno (pergunta, nível, histórico, contrato da intenção e
  material verificado).
- `tests/test_referencia_prompts.py` confere que os quatro arquivos têm todas as seções do Anexo B.

Ao alterar um prompt, regenere a documentação (`docs/agentes.md` e a seção 2 do relatório),
que reproduz o texto integral.

Regras permanentes (persona, segurança, idioma e formato público) ficam nos prompts.
A tarefa define intenção, nível, material, limite específico e se a pergunta da prática
é produzida pelo agente ou pelo sistema. A revisão do Guardião mantém seu contrato
JSON e recebe o escopo especial da avaliação sem receber gabaritos.
