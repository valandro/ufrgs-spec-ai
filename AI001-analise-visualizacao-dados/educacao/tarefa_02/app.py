# Bibliotecas usadas para preparar os dados, criar o gráfico e montar o dashboard.
import unicodedata

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

# URLs públicas usadas para que o aplicativo funcione em qualquer computador.
URL_DATASET = (
    "https://raw.githubusercontent.com/valandro/ufrgs-spec-ai/main/"
    "AI001-analise-visualizacao-dados/educacao_rs/datasets/dataset_principal.csv"
)
URL_REGIOES = (
    "https://raw.githubusercontent.com/valandro/ufrgs-spec-ai/main/"
    "AI001-analise-visualizacao-dados/educacao_rs/datasets/"
    "municipios_corede_regiao_funcional_rs.csv"
)

COLUNA_ESCOLARIDADE = "% dos ocupados com ensino médio completo 2010"
COLUNA_RENDA = "Rendimento médio dos ocupados 2010"
SALARIO_MINIMO_2010 = 510.00

# Faixas exibidas no filtro de renda.
FAIXAS_RENDA = [
    "Abaixo de 1 salário mínimo",
    "De 1 a menos de 2 salários mínimos",
    "De 2 a menos de 3 salários mínimos",
    "De 3 a menos de 4 salários mínimos",
    "De 4 a menos de 5 salários mínimos",
]

NOMES_REGIOES_FUNCIONAIS = {
    "RF1": "Metropolitana",
    "RF2": "Vales",
    "RF3": "Serra",
    "RF4": "Litoral Norte",
    "RF5": "Sul",
    "RF6": "Campanha e Fronteira Oeste",
    "RF7": "Noroeste e Missões",
    "RF8": "Central",
    "RF9": "Norte e Produção",
}

NOMES_COREDE = {
    "Metropolitano Delta do Jacuí": "Região Metropolitana de Porto Alegre",
}


def normalizar_nome(nome):
    """Cria uma chave consistente para cruzar nomes das duas bases."""
    nome = str(nome).replace(" (RS)", "").strip().lower()
    nome = unicodedata.normalize("NFKD", nome)
    nome = "".join(caractere for caractere in nome if not unicodedata.combining(caractere))
    return " ".join(nome.replace("'", "").split())


def classificar_renda(renda):
    """Classifica a renda média conforme múltiplos do salário mínimo de 2010."""
    if renda < SALARIO_MINIMO_2010:
        return FAIXAS_RENDA[0]
    if renda < 2 * SALARIO_MINIMO_2010:
        return FAIXAS_RENDA[1]
    if renda < 3 * SALARIO_MINIMO_2010:
        return FAIXAS_RENDA[2]
    if renda < 4 * SALARIO_MINIMO_2010:
        return FAIXAS_RENDA[3]
    return FAIXAS_RENDA[4]


@st.cache_data
def carregar_dados():
    """Carrega, limpa e cruza os indicadores com a classificação regional."""
    dados = pd.read_csv(URL_DATASET)
    regioes = pd.read_csv(URL_REGIOES)

    # Mantém somente municípios e converte os indicadores para números.
    dados = dados[
        ~dados["Territorialidades"].isin(["Brasil", "Rio Grande do Sul"])
    ].copy()
    dados[COLUNA_ESCOLARIDADE] = pd.to_numeric(
        dados[COLUNA_ESCOLARIDADE], errors="coerce"
    )
    dados[COLUNA_RENDA] = pd.to_numeric(dados[COLUNA_RENDA], errors="coerce")
    dados = dados.dropna(subset=[COLUNA_ESCOLARIDADE, COLUNA_RENDA])
    dados["faixa_renda"] = dados[COLUNA_RENDA].map(classificar_renda)
    dados["municipio"] = dados["Territorialidades"].str.replace(
        " (RS)", "", regex=False
    ).str.strip()
    dados["chave_municipio"] = dados["municipio"].map(normalizar_nome)

    # Prepara a tabela de COREDEs e Regiões Funcionais para o cruzamento.
    mapa_regioes = regioes[
        ["codigo_ibge", "municipio", "corede", "regiao_funcional", "regiao_funcional_id"]
    ].copy()
    mapa_regioes["regiao_funcional_nome"] = mapa_regioes["regiao_funcional"].map(
        NOMES_REGIOES_FUNCIONAIS
    )
    mapa_regioes["chave_municipio"] = mapa_regioes["municipio"].map(normalizar_nome)

    # O cruzamento por chave normalizada corrige diferenças de acentuação e grafia.
    mapa_regioes = mapa_regioes.drop(columns="municipio")
    dados = dados.merge(mapa_regioes, on="chave_municipio", how="inner")
    dados["corede_nome"] = dados["corede"].replace(NOMES_COREDE)
    return dados


@st.cache_data
def criar_grafico(dados, destacar_porto_alegre=False):
    """Cria o gráfico de dispersão e a reta de tendência."""
    dados = dados.copy()

    # Calcula os dois pontos extremos da reta de regressão linear.
    minimo_x = dados[COLUNA_ESCOLARIDADE].min()
    maximo_x = dados[COLUNA_ESCOLARIDADE].max()
    coeficiente_angular, intercepto = np.polyfit(
        dados[COLUNA_ESCOLARIDADE], dados[COLUNA_RENDA], 1
    )
    dados_linha = pd.DataFrame(
        {
            COLUNA_ESCOLARIDADE: [minimo_x, maximo_x],
            COLUNA_RENDA: [
                coeficiente_angular * minimo_x + intercepto,
                coeficiente_angular * maximo_x + intercepto,
            ],
            "tipo": "Reta de tendência",
        }
    )

    # Separa Porto Alegre para desenhá-la com uma cor diferente quando necessário.
    filtro_porto = (
        dados["chave_municipio"].eq("porto alegre")
        if destacar_porto_alegre
        else pd.Series(False, index=dados.index)
    )
    dados_pontos = dados.loc[~filtro_porto].copy()
    dados_pontos["tipo"] = "Municípios"
    dados_porto = dados.loc[filtro_porto].copy()
    dados_porto["tipo"] = "Porto Alegre"

    # Define as cores usadas na legenda conforme os elementos presentes no gráfico.
    tipos_legenda = ["Municípios"]
    if destacar_porto_alegre and not dados_porto.empty:
        tipos_legenda.append("Porto Alegre")
    tipos_legenda.append("Reta de tendência")

    cores_por_tipo = {
        "Municípios": "#6fa3cc",
        "Porto Alegre": "#168542",
        "Reta de tendência": "#a31313",
    }
    escala_cores = alt.Scale(
        domain=tipos_legenda,
        range=[cores_por_tipo[tipo] for tipo in tipos_legenda],
    )

    # A camada azul representa municípios, incluindo os tooltips informativos.
    pontos = alt.Chart(dados_pontos).mark_circle(
        size=55,
        opacity=0.65,
    ).encode(
        x=alt.X(
            f"{COLUNA_ESCOLARIDADE}:Q",
            title="Ocupados com ensino médio completo em 2010 (%)",
        ),
        y=alt.Y(
            f"{COLUNA_RENDA}:Q",
            title="Rendimento médio dos ocupados (R$)",
        ),
        color=alt.Color(
            "tipo:N",
            scale=escala_cores,
            legend=alt.Legend(title="Elementos do gráfico"),
        ),
        tooltip=[
            "municipio:N",
            "corede_nome:N",
            "regiao_funcional_nome:N",
            "faixa_renda:N",
            f"{COLUNA_ESCOLARIDADE}:Q",
            f"{COLUNA_RENDA}:Q",
        ]
    )

    # A camada verde destaca Porto Alegre quando ela faz parte da seleção.
    porto_alegre = alt.Chart(dados_porto).mark_circle(
        size=180,
        opacity=1,
    ).encode(
        x=alt.X(
            f"{COLUNA_ESCOLARIDADE}:Q",
            title="Ocupados com ensino médio completo em 2010 (%)",
        ),
        y=alt.Y(
            f"{COLUNA_RENDA}:Q",
            title="Rendimento médio dos ocupados (R$)",
        ),
        color=alt.Color(
            "tipo:N",
            scale=escala_cores,
            legend=alt.Legend(title="Elementos do gráfico"),
        ),
        tooltip=[
            "municipio:N",
            "corede_nome:N",
            "regiao_funcional_nome:N",
            "faixa_renda:N",
            f"{COLUNA_ESCOLARIDADE}:Q",
            f"{COLUNA_RENDA}:Q",
        ],
    )

    # A camada vermelha representa a tendência linear dos dados selecionados.
    reta = alt.Chart(dados_linha).mark_line(
        color="#a31313",
        size=3,
    ).encode(
        x=alt.X(
            f"{COLUNA_ESCOLARIDADE}:Q",
            title="Ocupados com ensino médio completo em 2010 (%)",
        ),
        y=alt.Y(
            f"{COLUNA_RENDA}:Q",
            title="Rendimento médio dos ocupados (R$)",
        ),
        color=alt.Color(
            "tipo:N",
            scale=escala_cores,
            legend=alt.Legend(title="Elementos do gráfico"),
        ),
    )

    return (
        (pontos + porto_alegre + reta)
        .properties(
            title="Todos os municípios: escolaridade versus rendimento médio",
            width="container",
            height=500,
        )
        .configure_axis(grid=True, gridColor="#d9d9d9")
    )


# Configuração geral da página Streamlit.
st.set_page_config(
    page_title="Escolaridade e rendimento no RS",
    page_icon="📊",
    layout="wide",
)

# Título e descrição apresentados ao usuário.
st.title("Escolaridade e rendimento dos municípios do Rio Grande do Sul")
st.write(
    "Explore a relação entre o percentual de ocupados com ensino médio completo "
    "e o rendimento médio dos ocupados em 2010."
)

# Carrega os dados uma vez e exibe uma mensagem amigável se houver falha.
try:
    dados = carregar_dados()
except Exception as erro:
    st.error(f"Não foi possível carregar os dados: {erro}")
    st.stop()

# Filtro múltiplo de regiões/COREDEs.
st.sidebar.header("Filtros")
contagem_regioes = (
    dados.groupby("corede")["municipio"]
    .nunique()
    .sort_index()
)
regioes_disponiveis = ["Todas"] + [
    f"{NOMES_COREDE.get(corede, corede)} ({quantidade} municípios)"
    for corede, quantidade in contagem_regioes.items()
]
regioes_selecionadas = st.sidebar.multiselect(
    "Escolha uma ou mais regiões (COREDE)",
    regioes_disponiveis,
    default=["Todas"],
)

# Filtro múltiplo baseado nas faixas de salário mínimo.
faixas_selecionadas = st.sidebar.multiselect(
    "Escolha uma ou mais faixas de renda",
    FAIXAS_RENDA,
    default=FAIXAS_RENDA,
)

# Filtro contínuo de escolaridade, com limites derivados dos dados reais.
minimo_escolaridade = round(float(dados[COLUNA_ESCOLARIDADE].min()), 2)
maximo_escolaridade = round(float(dados[COLUNA_ESCOLARIDADE].max()), 2)
faixa_escolaridade = st.sidebar.slider(
    "Escolaridade dos ocupados (%)",
    min_value=minimo_escolaridade,
    max_value=maximo_escolaridade,
    value=(minimo_escolaridade, maximo_escolaridade),
    step=0.01,
    key="filtro_escolaridade_v2",
)

# Aplica primeiro o filtro regional e decide se Porto Alegre deve ser destacada.
if not regioes_selecionadas or "Todas" in regioes_selecionadas:
    dados_filtrados = dados
    destacar_porto_alegre = True
else:
    nomes_coredes = [
        selecao.rsplit(" (", 1)[0]
        for selecao in regioes_selecionadas
    ]
    dados_filtrados = dados[dados["corede_nome"].isin(nomes_coredes)]
    destacar_porto_alegre = "Região Metropolitana de Porto Alegre" in nomes_coredes

# Aplica os filtros de escolaridade e de faixa de renda ao resultado regional.
dados_filtrados = dados_filtrados[
    dados_filtrados[COLUNA_ESCOLARIDADE].between(
        faixa_escolaridade[0], faixa_escolaridade[1]
    )
]

if faixas_selecionadas:
    dados_filtrados = dados_filtrados[
        dados_filtrados["faixa_renda"].isin(faixas_selecionadas)
    ]
else:
    dados_filtrados = dados_filtrados.iloc[0:0]

# Resumo do recorte atual e referência usada nas faixas de renda.
st.caption(
    f"{len(dados_filtrados)} municípios exibidos. "
    "A classificação regional cobre os municípios disponíveis no recorte de 2010."
)

st.caption(
    "Faixas de renda baseadas no salário mínimo de 2010 = R$ 510,00. "
    "Fonte: CONSTANZI, Rogério Nagamine; FIPE (2023)."
)

# Exibe o gráfico ou informa que a combinação de filtros não possui registros.
if dados_filtrados.empty:
    st.warning("Esse filtro não possui dados disponíveis.")
else:
    st.altair_chart(
        criar_grafico(dados_filtrados, destacar_porto_alegre),
        use_container_width=True,
    )

st.info(
    "Fonte: Atlas do Desenvolvimento Humano no Brasil, Censo 2010. "
    "O mapeamento regional usa a tabela completa de municípios, COREDEs e "
    "Regiões Funcionais de Planejamento do RS."
)
