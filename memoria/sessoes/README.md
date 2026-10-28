# Historico de sessoes da memoria

Este diretorio armazena um arquivo JSON por sessao de conversa, contendo o
historico de turnos (pergunta, resposta, agente responsavel, timestamp).

Os arquivos sao criados automaticamente em tempo de execucao pelo modulo
`agente/memoria.py`. Nao e necessario criar nada aqui manualmente.

Memoria != conhecimento factual: informacoes ditas pelo modelo em turnos
anteriores nao sao tratadas automaticamente como verdade; o Guardiao
reavalia a confiabilidade a cada turno.
