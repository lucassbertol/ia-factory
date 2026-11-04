# Guardião como decisão de entrega

Desenho proposto na conversa e autorizado pelo pedido de implementação:
respostas geradas só são entregues após aprovação. Reprovação fundamentada
permite uma rodada de correção dos autores afetados, seguida de nova revisão
do conjunto. Erro persistente, análise inconclusiva ou formato inválido levam
a mensagem determinística de impossibilidade de validação, sem os rascunhos.

Usar JSON com veredito APROVADO/REPROVADO/INCONCLUSIVO e até 3 problemas.
Erro factual exige autor, trecho real, citação real da base e correção.
Incompletude exige autor, trecho do pedido original e correção solicitada.
O código confere a presença das citações; o julgamento semântico continua sendo
responsabilidade do modelo e não é uma garantia absoluta de correção.

Alternativas: apenas ligar o parâmetro antigo (descartada: sem segunda revisão);
repetir até aprovar (descartada: latência e ciclos); uma rodada com saída segura
(escolhida). Preservar referências, memória, CLI/web e caminhos sem modelo.
A variável MAX_REESCRITAS_GUARDIAO passa a padrão 1, limitada a 0 ou 1; 0 só
desliga a tentativa de correção, nunca o bloqueio. Não fazer novas chamadas
automáticas de guardrail dentro da reescrita. Registrar decisões e tentativas,
mas guardar na resposta da sessão apenas conteúdo aprovado ou orientação segura.
