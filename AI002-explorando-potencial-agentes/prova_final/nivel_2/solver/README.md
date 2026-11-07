# Solver ARC-AGI-1 — Nível 2

Resolve as 20 tarefas de `tarefas/tarefas.txt` com o Gemini 3.5 Flash Lite, com raciocínio alto, de duas formas:

- **Fim a fim:** o modelo devolve a grade de saída em JSON.
- **Geração de código:** o modelo escreve `transform(grid)`. O programa roda em um processo separado, com tempo limite de 10 s, nos exemplos de treino e na entrada de teste.

## Como rodar

Todos os comandos rodam a partir da pasta raiz da entrega, a que contém `solver/`, `tarefas/` e `requirements.txt`.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env              # e coloque a chave em GOOGLE_API_KEY

.venv/bin/python -m solver --teste-rapido   # 2 tarefas, 4 chamadas, grava em resultados_teste/
.venv/bin/python -m solver                  # experimento completo: 20 tarefas, 40 chamadas
```

Se a execução parar no meio, rode o mesmo comando de novo. As tarefas já gravadas são puladas e não gastam cota.
Para refazer do zero, apague a pasta `resultados/`.

Testes, sem chamar a API:

```bash
.venv/bin/python -m unittest discover -s tests -v
```

Figuras do relatório, a partir dos JSON das tarefas. Esse script usa matplotlib, que o solver não usa:

```bash
.venv/bin/pip install matplotlib
.venv/bin/python figuras/gerar_figuras.py
```

## Saídas em `resultados/`

| Arquivo | Conteúdo |
|---|---|
| `fim_a_fim.csv`, `codigo.csv` | Uma linha por tarefa: modelo, nível de raciocínio, resolvida, treino_ok, erro, tokens de entrada, raciocínio e saída, segundos |
| `resumo.json`, `resumo.md` | Totais por abordagem: modelo, nível de raciocínio, resolvidas, tokens, tempo e, no código, quantas acertaram todo o treino |
| `respostas/<abordagem>/` | Resposta bruta do modelo para cada tarefa, `.txt` no fim a fim e `.py` no código |

## Organização

| Módulo | Responsabilidade |
|---|---|
| `main.py` | Lê as tarefas, roda as abordagens, grava CSV e resumo |
| `abordagens.py` | Prompts, leitura do JSON e do código, comparação com a resposta |
| `executor.py` | Roda `transform(grid)` em subprocesso com tempo limite |
| `llm.py` | Cliente Gemini: pausa de 1 s, retentativas para erros 429 e 5xx, contagem de tokens |

## Decisões

- **Prompts iguais aos do nível 1**, para comparar os dois níveis.
- **Tempo por tarefa** é a duração da chamada que deu certo mais a execução do código. As esperas de retentativa ficam de fora, como no notebook do nível 1.
- **Uma chamada que falha** após 5 tentativas não é gravada. Rodar de novo tenta essa tarefa outra vez.
- **O subprocesso isola falhas, mas não é uma sandbox de segurança.** O código gerado ainda pode acessar arquivos e rede.
- **Modelo e nível de raciocínio ficam em cada linha.** O solver se recusa a retomar um arquivo gravado com outra configuração, para não somar execuções diferentes.
- **Nota sobre os resultados entregues:** o experimento rodou antes de essas duas colunas existirem, com a configuração padrão, `gemini-3.5-flash-lite` e raciocínio `high`. As colunas foram preenchidas depois com esses valores, sem alterar nenhuma medida. Os tokens de raciocínio, diferentes de zero em todas as tarefas, são compatíveis com o raciocínio alto.
- **A chave fica em `.env`**, que o `.gitignore` exclui. Ela nunca aparece no código nem no relatório.
