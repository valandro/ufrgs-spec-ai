# Escolaridade, renda e produção nos municípios do RS — dashboard

Atividade 02 da disciplina IA001: dashboard em Streamlit que dá continuidade à
Atividade 01 e investiga as suas quatro perguntas nos 496 municípios gaúchos, com
dados do Censo 2010. Há uma página por pergunta, e os filtros de Região Funcional e
COREDE, na barra lateral, valem para todas.

As perguntas, as visualizações, os resultados e as limitações estão no notebook de
registro, `atividade02_dashboard_streamlit.ipynb`.

## Instalação e execução

Requer Python 3.10 ou mais recente e acesso à internet para instalar as dependências.
Depois de extrair o ZIP, abra um terminal na pasta `atividade02/` que contém este
README. A aplicação fica em `dashboard/`.

### Windows (PowerShell)

O comando `py` é instalado junto com o Python pelo instalador oficial. Os comandos
abaixo usam diretamente o Python do ambiente virtual, sem exigir a ativação dele:

```powershell
cd .\dashboard
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Se `py` não for reconhecido, instale o Python 3.10 ou mais recente e marque a opção
para instalar o Python Launcher. Se o terminal estiver na pasta acima daquela que
contém este README, entre primeiro nela com `cd .\atividade02`.

### macOS e Linux

```bash
cd dashboard
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

O navegador abre em `http://localhost:8501`. Os dados já estão em `dashboard/dados/`,
então não é preciso baixar nada; só as bibliotecas JavaScript do mapa (Leaflet) vêm da
internet.

> Ao alterar `analise.py`, `comum.py`, os arquivos de gráficos ou `.streamlit/config.toml`,
> **pare o Streamlit (Ctrl+C) e rode `streamlit run app.py` de novo**: ele não recarrega
> os módulos importados pelas páginas nem o tema. Mudanças só em `paginas/` aparecem ao
> atualizar o navegador.

Para conferir que os cálculos reproduzem os valores das Atividades 01 e 02 (o script
falha se algum divergir), também de dentro de `dashboard/`:

```bash
python analise.py
```

## Arquivos

```text
atividade02/
├── README.md
├── atividade02_dashboard_streamlit.ipynb   # registro do grupo (entrega da atividade)
└── dashboard/
    ├── .streamlit/config.toml    # tema: cor dos controles
    ├── app.py                    # entrada: navegação entre páginas + filtros da barra lateral
    ├── comum.py                  # peças de todas as páginas: cartões, mapa, tabela, rodapé
    ├── paginas/
    │   ├── inicio.py             # público, as 4 perguntas, como usar
    │   ├── p1_escolaridade_renda.py
    │   ├── p2_faixas_de_renda.py
    │   ├── p3_capital.py
    │   └── p4_renda_producao.py
    ├── analise.py                # cálculos das 4 perguntas + autoverificação
    ├── graficos_atividade01.py   # gráficos da Atividade 01 (Matplotlib)
    ├── graficos_interativos.py   # gráficos interativos (Altair)
    ├── regioes_funcionais_rs.ipynb  # gera os dois GeoJSON a partir das fontes oficiais
    ├── requirements.txt
    └── dados/
        ├── municipios_web.geojson   # 497 municípios, indicadores de 2010
        └── regioes_web.geojson      # 9 Regiões Funcionais dissolvidas
```

## Como refazer os dados

Os dois GeoJSON são gerados por `dashboard/regioes_funcionais_rs.ipynb`. Para
refazê-los a partir das fontes oficiais, execute o notebook inteiro a partir de
`dashboard/`: a seção 9 grava as cópias em `dados/` e registra a procedência de cada
fonte (URL, data e SHA-256) em `dados/regioes_funcionais/preparados/fontes_e_preparo.json`.

## Fontes

- Atlas do Desenvolvimento Humano no Brasil (Pnud, Ipea, FJP), com dados do Censo 2010 (IBGE) — rendimento, escolaridade e faixas de rendimento dos ocupados.
- PIB dos municípios 2010 (IBGE, SIDRA tabela 5938) — PIB per capita, população e valor adicionado por setor.
- Malha municipal 2022 (IBGE).
- Regiões Funcionais de Planejamento e COREDEs — Decreto 54.572/2019 (SEPLAG-RS).
