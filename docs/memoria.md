# Memória da conversa

Implementação: `agente/memoria.py` (`MemoriaConversa`). Justificativa: seção 3.3 do relatório.

## Onde fica

Um arquivo JSON por sessão em `memoria/sessoes/<id>.json` (ignorado pelo Git). A pasta pode ser
trocada pela variável de ambiente `AGENTE_MEMORIA_DIR` (os testes usam uma pasta temporária).

- `python -m agente "pergunta"` usa a sessão `default`; o modo interativo usa `interativo`.
- `--sessao ID` escolhe ou retoma uma conversa (1 a 64 letras ASCII, números, `_` ou `-`).
- `--sessao ID --limpar-sessao` apaga a sessão e encerra.

## Campos de cada turno

| Campo | Uso |
|---|---|
| `timestamp`, `pergunta`, `resposta` | registro da conversa |
| `intencao` | continuidade ("sim", "e por quê?") e tópicos do fechamento |
| `agente`, `agentes` | quem respondeu (`regra_deterministica` nas recusas) |
| `tipo` | `resposta` (modelo) ou `orientacao` (resposta fixa, exercício ou fallback após bloqueio) |
| `exercicio_pendente` | enunciado da atividade em andamento, usado para avaliar tentativas |
| `revisao` | decisão final, problemas, tentativas, reescrita e bloqueio; rascunhos não substituem a resposta entregue |
| `nivel` | nível declarado (`--nivel` ou "sou iniciante") |
| `exemplo` | exemplo Java verificado mostrado, para variar no próximo pedido |
| `exercicio`, `exercicio_concluido` | identificador da atividade e conclusão indicada pelo avaliador |
| `duracao_segundos` | tempo do turno |

## Como entra nos prompts

O histórico só é enviado quando a pergunta depende dele (tentativa de exercício, "no exemplo
anterior", continuações curtas). Ele entra marcado como "dados, não instruções", sem timestamps
e com o código das respostas anteriores trocado por `[código omitido]`, limitado a
`MAX_CONTEXTO_CARACTERES` (2000). Metade desse espaço fica reservada ao enunciado do exercício
em andamento. O Guardião não recebe o histórico: ele julga só contra a referência local.

## Por que não a memória do CrewAI

A memória nativa do CrewAI depende de um modelo de embeddings e, sem configuração, usa o da
OpenAI, o que exigiria chave de API e violaria a regra de custo zero. Além disso, o comando
obrigatório encerra após cada pergunta, então o estado precisa estar em disco.

## Limites

- Uso sequencial: evite gravar na mesma sessão pela CLI e pela web ao mesmo tempo.
- Não há busca semântica no histórico; só os turnos mais recentes cabem no contexto.
- JSONs antigos continuam aceitos (campos ausentes são inferidos).

Turnos com `revisao.bloqueada=true` preservam o exercício pendente e não contam
como tópicos estudados. A intenção original permanece no registro para auditoria.

Nas avaliações dos exercícios cadastrados, o fluxo monta um contexto específico:
enunciado, tentativas anteriores desde a proposta e a última pergunta feita ao
estudante. Não inclui respostas anteriores completas do sistema nesse contexto,
para reduzir a cópia pelo modelo. O avaliador em Python recebe as tentativas
acumuladas; seus fatos orientam o texto do Inquiridor e a revisão do Guardião.
