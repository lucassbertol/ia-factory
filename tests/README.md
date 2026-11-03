# Coleta das perguntas obrigatórias do PDF

O único script desta pasta, `test_perguntas_pdf.py`, faz as oito perguntas
obrigatórias de Factory Method: conceito, exemplo Java, quando usar/evitar,
uso incorreto, conceitos equivocados, duas perguntas de anti-alucinação e
fechamento. Ele chama o fluxo real do projeto e registra as respostas completas.

## Preparação

Abra um terminal na raiz do projeto e ative seu ambiente virtual. Se estiver
usando o ambiente `.venvcle` existente, no Linux:

```bash
source .venvcle/bin/activate
```

Se ainda precisar instalar as dependências, com o ambiente ativado:

```bash
python -m pip install -r requirements.txt
```

Inicie o Ollama em outro terminal:

```bash
ollama serve
```

Verifique se o modelo está disponível:

```bash
ollama list
```

Caso não esteja, baixe-o antes de executar a coleta:

```bash
ollama pull qwen2.5:3b
```

O script usa o modelo configurado pelo projeto, por padrão `qwen2.5:3b`.
Se o Ollama já estiver ativo, não é necessário iniciar outro servidor.

## Executar no futuro

Na raiz do projeto, execute:

```bash
python tests/test_perguntas_pdf.py
```

As perguntas são feitas em sequência. Cada uma usa uma sessão nova para evitar
interferência de conversas antigas ou de um exercício pendente. As sessões
geradas ficam em `memoria/sessoes/`, ignoradas pelo Git.

As recusas dos dois pedidos de anti-alucinação são capturadas como respostas
do sistema; essas recusas podem ocorrer antes da chamada ao modelo.

## Resultado

O arquivo será salvo em:

```text
evidencias/respostas_teste.json
```

Ele contém as perguntas, categorias, respostas sem truncamento, identificadores
de sessão, duração e eventuais erros. O campo `modelo` identifica o modelo
configurado quando o sistema carrega corretamente. Datas são registradas em UTC.

Cada execução substitui esse JSON. Copie o arquivo antes de repetir se quiser
preservar uma coleta anterior. O script salva o progresso após cada pergunta;
se uma falhar, registra o erro e continua. Ctrl+C preserva o que já foi coletado
e identifica as perguntas não executadas.

Os estados por pergunta são `nao_executada`, `em_execucao`, `respondida`,
`recusa`, `erro` e `interrompida`. Código de saída 0 indica coleta concluída;
1 indica erro; 130 indica interrupção. Concluir a coleta não significa que as
respostas estejam conceitualmente corretas: o julgamento deve ser feito depois.


