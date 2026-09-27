# Dashboard da Atividade 02

Dashboard interativo para explorar a relação entre escolaridade e rendimento médio dos municípios do Rio Grande do Sul.

Esta pasta é a unidade da aplicação. Para publicar no GitHub ou enviar para avaliação,
mantenha juntos `app.py`, `requirements.txt` e este `README.md`.

## Requisitos

- Python 3.10 ou superior
- Acesso à internet para carregar os arquivos CSV do GitHub

## Como executar

Abra o terminal nesta pasta e execute:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

O Streamlit abrirá o dashboard no navegador, normalmente em:

```text
http://localhost:8501
```

## Dados

O aplicativo carrega os dados diretamente do repositório público do grupo:

- Indicadores de escolaridade e rendimento: Atlas do Desenvolvimento Humano, Censo 2010.
- Classificação municipal: tabela completa de municípios, COREDEs e Regiões Funcionais de Planejamento do RS.

O filtro regional usa os nomes dos COREDEs, como `Vale do Taquari` e
`Região Metropolitana de Porto Alegre`. Também há filtros múltiplos por região e
faixa de renda, além de um intervalo de escolaridade.

A tabela de classificação contém 497 municípios oficiais; o dataset do Censo 2010
utilizado na análise contém 496 municípios.

## Observação

Para avaliar o dashboard, é necessário executar o comando `python -m streamlit run app.py`.
Abrir o arquivo `app.py` diretamente não exibe a aplicação.
