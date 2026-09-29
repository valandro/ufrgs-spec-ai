"""Dashboard da Atividade 02 — escolaridade, renda e produção nos municípios do RS.

Executar com:  streamlit run app.py

Este arquivo é só a entrada: configura a página, desenha os filtros comuns na
barra lateral e monta a navegação. Cada pergunta é uma página em `paginas/`,
e as peças que elas compartilham (mapa, cartões, tabela) estão em `comum.py`.
"""

import streamlit as st

import comum

st.set_page_config(page_title="Escolaridade e renda no RS", page_icon="🗺️", layout="wide")

# ---------------------------------------------------------------------------
# Navegação — uma página por pergunta, com endereço próprio
# ---------------------------------------------------------------------------
paginas = [
    st.Page("paginas/inicio.py", title="Início", icon=":material/home:", default=True),
    st.Page("paginas/p1_escolaridade_renda.py", title="Escolaridade × renda",
            icon=":material/school:", url_path="escolaridade-renda"),
    st.Page("paginas/p2_faixas_de_renda.py", title="Faixas de renda",
            icon=":material/stacked_bar_chart:", url_path="faixas-de-renda"),
    st.Page("paginas/p3_capital.py", title="Proximidade da capital",
            icon=":material/location_on:", url_path="proximidade-da-capital"),
    st.Page("paginas/p4_renda_producao.py", title="Renda × produção ✨",
            icon=":material/factory:", url_path="renda-producao"),
]
pagina = st.navigation(paginas, position="top")

# ---------------------------------------------------------------------------
# Filtros comuns — ficam aqui para valer em todas as páginas. Como este arquivo
# roda em qualquer página, a seleção se mantém ao trocar de pergunta.
# ---------------------------------------------------------------------------
try:
    mun = comum.carregar()[0]
except FileNotFoundError as erro:
    st.error(str(erro))
    st.stop()

st.sidebar.header("Filtros")
todas = comum.todas_rf(mun)
rfs = st.sidebar.multiselect("Região Funcional", todas, default=todas, key="rfs")

coredes_disponiveis = sorted(mun.loc[mun["regiao_funcional"].isin(rfs), "corede"].unique())
# Ao desmarcar uma região, os COREDEs dela saem da seleção em vez de gerar erro.
if "coredes" in st.session_state:
    st.session_state.coredes = [c for c in st.session_state.coredes if c in coredes_disponiveis]
st.sidebar.multiselect(
    "COREDE", coredes_disponiveis, key="coredes",
    placeholder="Todos das regiões escolhidas",
    help="Só aparecem os COREDEs das Regiões Funcionais escolhidas acima.")

st.sidebar.divider()
st.sidebar.caption(
    "Os filtros valem para todas as páginas. Os cortes (retas, tercis/quartis/quintis, "
    "desvios-padrão) são calculados sobre os 496 municípios do RS e **não mudam com o filtro**: "
    "ele só escolhe o que aparece.")

pagina.run()
