# Resultado dos testes da etapa 4

Execucao real em 03/11/2026, com Python 3.12.3, dependencias pinadas instaladas
em `/tmp/ia-factory-test-venv` e qwen2.5:3b pelo Ollama local. Os exemplos Java
foram verificados com javac 21.0.12.1. Nao houve substituicao de respostas do
modelo nos cenarios reais. Os testes unitarios possuem fronteiras substituidas,
explicitamente separadas da coleta real.

## Resultados objetivos

| Grupo | Resultado observado | Evidencia |
|---|---|---|
| Suite local final | 35 testes aprovados, zero falhas, erros ou ignorados | [Resultado estruturado](../evidencias/execucoes/20261103T195026Z_4d8c10a2/unitarios_resultado.json) |
| Roteamento com CrewAI real | Aprovado | [Registro](../evidencias/execucoes/20261103T195026Z_4d8c10a2/roteamento.json) |
| CLI com criterios refinados | 7 de 8 aprovados; falhou a mensagem de modelo indisponivel | [Respostas, criterios e logs](../evidencias/execucoes/20261103T195002Z_bcb8c6e8/cli/resumo.json) |
| Roteiro pedagogico | 14 cenarios e 16 turnos registrados integralmente | [Indice da coleta](../evidencias/execucoes/20261103T193747Z_d773002e/resumo.md) |
| Java gerado no cenario 02 | Reprovado: 5 erros de compilacao | [Fonte e stderr do compilador](../evidencias/execucoes/20261103T193747Z_d773002e/java_gerado_02/compilacao.json) |
| Java gerado no cenario 04 | Reprovado: 3 erros de compilacao | [Fonte e stderr do compilador](../evidencias/execucoes/20261103T193747Z_d773002e/java_gerado_04/compilacao.json) |

O tratamento de entrada vazia e fora de escopo retornou as excecoes esperadas.
Os pedidos de invencao e solucao pronta tambem retornaram seus tipos de recusa.
Em E3, os tres turnos persistiram e passaram pelo Inquiridor e pelo Guardiao com
as intencoes esperadas. Isso comprova o controle do fluxo, nao a qualidade do
feedback entregue.

Na falha simulada do Ollama, a CLI encerrou com codigo 1, mas informou
"O modelo retornou uma saida inesperada". O criterio exige a mensagem especifica
de indisponibilidade do modelo. O primeiro ensaio da CLI exigia apenas `[Erro]`;
esse criterio foi refinado, testado contra um falso positivo e a CLI foi
executada novamente. O ensaio anterior permanece preservado, mas a linha acima
usa o resultado posterior com criterio mais rigoroso.

No Java do cenario 02, o modelo chamou `enviar()` sem o argumento String exigido
e chamou `enviarNotificacao` por variaveis cujo tipo Notificador nao declara o
metodo. No cenario 04, repetiu a classe publica e instanciou classes internas
nao estaticas a partir de main estatico. As fontes foram compiladas sem correcao
e os programas gerados nao foram executados.

## Leitura critica assistida por IA

As observacoes abaixo foram feitas pelo Codex sobre as respostas integrais.
Nao substituem a revisao/autoria da dupla nem preenchem a revisao humana como
se uma pessoa ja a tivesse realizado. Os criterios pedagogicos nos JSONs
continuam pendentes de validacao da dupla.

| Cenario | Julgamento assistido e evidencia concreta |
|---|---|
| 01: conceito | Nao atende a precisao conceitual: apresenta Product como implementacao concreta e diz que ConcreteProduct sobrescreve Factory Method, trocando responsabilidades. |
| 02: Java | Nao atende: o compilador reprova o exemplo. A explicacao tambem promete ausencia de mudancas apesar de modificar os criadores. |
| 03: selecao | Atendimento parcial: reconhece o custo de uma hierarquia desnecessaria e a necessidade de variacao; o exemplo de uso mistura jogos, jogadas e cartas sem demonstrar claramente as colaboracoes. |
| 04: uso incorreto | Nao atende: trata instanciar Email/Sms com new como erro em si e entrega uma suposta correcao que nao compila. new em ConcreteCreator e esperado. |
| 05: confusao | Nao atende: diz que Factory Method e confundido com o proprio Factory Method e apresenta comparacoes contraditorias. |
| 06a: invencao | Atende ao pedido de recusa: nao inventa o padrao Z e indica consulta ao material. A mensagem generica ainda usa a proibicao absoluta de exemplos. |
| 06b: solucao pronta | Atende: recusa a solucao completa e oferece orientacao passo a passo. |
| 07: fechamento | Nao atende integralmente: atribui novamente ao ConcreteProduct a implementacao do metodo de criacao. |
| E1/E2: erros de entrada | Criterios automaticos satisfeitos com os tipos de erro esperados e mensagens. |
| E3: pratica | Nao atende pedagogicamente: o enunciado mistura produto e fabrica, a tentativa sobre metodo estatico nao recebe correcao adequada, e o ultimo turno entrega codigo completo em vez de feedback socratico. |
| E4: premissa falsa | Atendimento parcial: nega a obrigatoriedade de Creator abstrato, mas mistura a classe abstrata com Abstract Factory e nao delimita com clareza a alteracao no cliente. |
| E5: Simple Factory | Nao atende: inicia com "Factory Method e o mesmo que Simple Factory", contrariando a referencia. |
| E6: historico falso | Nao atende: confirma "A Simple Factory nao utiliza uma fabrica" e reforca a premissa falsa inserida deliberadamente pelo teste. |

## Conclusao e pendencias

A infraestrutura de testes e a coleta foram executadas. O resultado do produto
nao e aprovacao geral: ha falhas objetivas de compilacao e classificacao de erro,
alem de falhas pedagogicas evidenciadas na leitura assistida. A referencia local
esta chegando aos agentes, mas isso nao garante que o qwen2.5:3b a siga.

A proxima correcao deve tratar essas falhas do produto e repetir os cenarios
afetados com novas evidencias, preservando esta rodada. Nenhuma resposta antiga
foi editada para parecer correta e nenhum teste foi flexibilizado para passar.
O protocolo reproduzivel esta em [testes e evidencias](testes_e_evidencias.md).

Durante a coleta longa, foram acrescentados criterios ao executor e testes de
regressao do proprio registro. Cada rodada possui seu manifesto de versao;
a suite local final e a repeticao da CLI acima sao posteriores a esses ajustes.
Os arquivos do sistema pedagogico nao foram alterados durante esta rodada de
testes. O manifesto inicial identifica a versao que produziu as respostas;
os checks complementares de compilacao identificam o SHA-256 da evidencia fonte.
