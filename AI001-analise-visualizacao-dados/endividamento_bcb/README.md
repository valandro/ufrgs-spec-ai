# Coletor SGS/BCB — Endividamento das Famílias

Script em Python que consome a API de séries temporais do Banco Central
(SGS/BCData) e gera um CSV. Por padrão coleta a **série 29038** —
endividamento das famílias com o SFN, exceto crédito habitacional, em relação
à renda acumulada dos últimos 12 meses (% a.a., frequência mensal).

## Requisitos

- Python 3.8 ou superior.
- Nenhuma dependência externa (usa apenas a biblioteca padrão).

## Uso

```bash
python endividamento_bcb.py [opções]
```

### Opções

| Opção            | Atalho | Padrão                         | Descrição |
|------------------|--------|--------------------------------|-----------|
| `--inicio`       | `-i`   | início da série                | Data inicial no formato `dd/MM/aaaa`. |
| `--fim`          | `-f`   | dado mais recente              | Data final no formato `dd/MM/aaaa`. |
| `--serie`        | `-s`   | `29038`                        | Código de qualquer série do SGS. |
| `--saida`        | `-o`   | `endividamento_familias.csv`   | Caminho do CSV de saída. |
| `--agrupar`      | `-g`   | `ano`                          | `ano` (agregado anual) ou `mes` (dado bruto). |
| `--excel-br`     |        | desligado                      | CSV com `;` e vírgula decimal, para Excel PT-BR. |

## Exemplos

Agregado anual de 2015 a 2020:

```bash
python endividamento_bcb.py -i 01/01/2015 -f 31/12/2020 -o endiv_anual.csv
```

Dado mensal bruto, série completa:

```bash
python endividamento_bcb.py --agrupar mes -o endiv_mensal.csv
```

Abrir direto no Excel em português:

```bash
python endividamento_bcb.py --excel-br -o endiv_para_excel.csv
```

Reaproveitar o script para outra série do SGS (ex.: 20714):

```bash
python endividamento_bcb.py -s 20714 --agrupar mes -o serie_20714.csv
```

## Formato de saída

**Agrupado por ano** (`--agrupar ano`):

| Coluna         | Descrição |
|----------------|-----------|
| `ano`          | Ano de referência. |
| `qtd_meses`    | Quantidade de observações mensais no ano. |
| `media`        | Média dos valores mensais (4 casas). |
| `minimo`       | Menor valor do ano. |
| `maximo`       | Maior valor do ano. |
| `ultimo_valor` | Valor do último mês disponível do ano. |

**Bruto por mês** (`--agrupar mes`): `data` (YYYY-MM-DD), `ano`, `mes`, `valor`.

## Observações

- Na API, `valor` chega como string com ponto decimal e `data` no dia 1º do
  mês (a série é mensal — o dia é apenas marcador).
- Sem `--inicio`/`--fim`, a série histórica completa é retornada.
- O CSV é gravado em `utf-8-sig` para abrir corretamente no Excel.