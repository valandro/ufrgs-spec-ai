"""Dashboard da Atividade 02 — escolaridade, renda e produção nos municípios do RS.

Executar com:  streamlit run app.py
"""

import folium
import geopandas as gpd
import numpy as np
import pandas as pd
import streamlit as st
from branca.element import MacroElement
from jinja2 import Template

import analise as an
import graficos_atividade01 as g1
from analise import ESCOLARIDADE, PIB, POPULACAO, RENDA, DISTANCIA

st.set_page_config(page_title="Escolaridade e renda no RS", page_icon="🗺️", layout="wide")

PERGUNTAS = {
    "P1": "1 · Escolaridade × renda",
    "P2": "2 · Faixas de renda por escolaridade",
    "P3": "3 · Proximidade da capital",
    "P4": "4 · Renda × produção local (novidade)",
}
ENUNCIADOS = {
    "P1": "Municípios onde mais ocupados têm ensino médio completo pagam melhor?",
    "P2": "Como muda a distribuição de faixas de renda conforme o nível de escolaridade do município?",
    "P3": ("A proximidade da capital explica o rendimento médio dos ocupados, ou há regiões "
           "não metropolitanas com rendimento equivalente ou superior?"),
    "P4": ("Existem municípios cuja renda dos residentes é incompatível com sua produção local, "
           "e o que os distingue dos demais de PIB igualmente baixo?"),
}
COMO_LER = {
    "P1": ("O mapa mostra quanto a renda de cada município se afasta da **renda esperada pela "
           "escolaridade** (a reta do gráfico 6.1). Quanto mais escuro, mais o município paga acima "
           "do que a escolaridade sugere; os tons claros ganham menos do que o esperado. As duas "
           "pontas passam de 1 desvio-padrão — são os casos a investigar dentro de cada COREDE."),
    "P2": ("O mapa pinta cada município pelo **quartil de escolaridade** dos ocupados — os mesmos "
           "quartis do gráfico 6.2.1, com limites calculados sobre o estado inteiro."),
    "P3": ("O mapa pinta a **renda em quintis**. Os anéis marcam 100, 200 e 300 km de Porto "
           "Alegre: se a proximidade explicasse a renda, os tons escuros se concentrariam no "
           "centro. Contornos: Metropolitana (traço cheio) e Serra e Hortênsias (tracejado)."),
    "P4": ("O mapa mostra quanto a renda se afasta da **renda esperada pelo PIB per capita**. "
           "Quanto mais escuro, mais a renda supera o que o PIB per capita faria esperar; os tons "
           "claros produzem muito e a renda não fica com os residentes. Contorno preto: os "
           "municípios do tercil inferior de PIB com renda acima do esperado."),
}
# Origem de cada mapa: P1 e P2 não tinham mapa na Atividade 01; P3 e P4 tinham um
# mapa estático em matplotlib, que aqui vira interativo.
ORIGEM_MAPA = {
    "P1": "Novo nesta atividade",
    "P2": "Novo nesta atividade",
    "P3": "Versão interativa do mapa 6.3.3 da Atividade 01",
    "P4": "Versão interativa do mapa 6.4.4 da Atividade 01",
}
NOVIDADE_P4 = (
    "**Novidade.** Esta pergunta não estava entre as três perguntas da proposta original da "
    "Atividade 01. Ela foi acrescentada em `atividade01_dados_pib_2010.ipynb` com um terceiro "
    "conjunto de dados — o **PIB dos municípios de 2010 (IBGE)**, que traz PIB per capita, "
    "população e valor adicionado por setor — e é a única que cruza a renda dos moradores com a "
    "produção local.")
FONTES = ("Fontes: Atlas do Desenvolvimento Humano no Brasil (Pnud, Ipea, FJP), Censo 2010 (IBGE); "
          "PIB dos municípios 2010 (IBGE); malha municipal 2022 (IBGE); Regiões Funcionais e "
          "COREDEs — Decreto 54.572/2019 (SEPLAG-RS).")


@st.cache_data(show_spinner="Carregando os municípios…")
def carregar():
    municipios, regioes = an.carregar()
    municipios, modelos = an.calcular(municipios)
    return municipios, regioes, modelos, an.testes_p4(municipios)


try:
    mun, regioes, modelos, p_valores_p4 = carregar()
except FileNotFoundError as erro:
    st.error(str(erro))
    st.stop()

com_dado = mun[RENDA].notna()


# ---------------------------------------------------------------------------
# Controles
# ---------------------------------------------------------------------------
st.sidebar.header("Controles")
pergunta = st.sidebar.radio("Pergunta", list(PERGUNTAS), format_func=PERGUNTAS.get)

todas_rf = sorted(mun["regiao_funcional"].unique(), key=lambda n: int(n[2:n.index(" ")]))
rfs = st.sidebar.multiselect("Região Funcional", todas_rf, default=todas_rf)

coredes_disponiveis = sorted(mun.loc[mun["regiao_funcional"].isin(rfs), "corede"].unique())
# Ao desmarcar uma região, os COREDEs dela saem da seleção em vez de gerar erro.
if "coredes" in st.session_state:
    st.session_state.coredes = [c for c in st.session_state.coredes if c in coredes_disponiveis]
coredes = st.sidebar.multiselect(
    "COREDE", coredes_disponiveis, key="coredes",
    placeholder="Todos das regiões escolhidas",
    help="Só aparecem os COREDEs das Regiões Funcionais escolhidas acima.")

so_tercil = False
if pergunta == "P4":
    so_tercil = st.sidebar.checkbox(
        "Só o tercil inferior de PIB per capita",
        help=f"Os 166 municípios com PIB per capita até "
             f"{an.reais(modelos.p4_corte_tercil)}/hab. — o recorte da 2ª metade da pergunta.")

st.sidebar.divider()
st.sidebar.caption(
    "Os cortes (retas, quartis, quintis, desvios-padrão) são calculados sobre os 496 municípios "
    "do RS e **não mudam com o filtro**: ele só escolhe o que aparece.")

selecao = mun["regiao_funcional"].isin(rfs)
if coredes:
    selecao &= mun["corede"].isin(coredes)
if so_tercil:
    selecao &= mun["tercil_inferior_pib"]
sel = mun[selecao & com_dado]


# ---------------------------------------------------------------------------
# Cabeçalho
# ---------------------------------------------------------------------------
st.title("Escolaridade, renda e produção nos municípios do RS")
st.caption("Censo 2010 · 496 municípios · para técnicos de planejamento regional (COREDEs, "
           "SEPLAG-RS e secretarias municipais)")
st.subheader(ENUNCIADOS[pergunta])
if pergunta == "P4":
    st.info(NOVIDADE_P4, icon="✨")

if not rfs:
    st.info("Nenhuma Região Funcional selecionada. Escolha ao menos uma na barra lateral.")
    st.stop()
if sel.empty:
    st.info("A combinação de filtros não deixou nenhum município com dado. "
            "Amplie a seleção de regiões ou de COREDEs, ou desmarque o tercil inferior de PIB.")
    st.stop()


# ---------------------------------------------------------------------------
# Indicadores da seleção
# ---------------------------------------------------------------------------
def indicadores():
    renda_sel, renda_rs = sel[RENDA].median(), mun.loc[com_dado, RENDA].median()
    delta_renda = (f"{an.reais(renda_sel - renda_rs, sinal=True)} vs. mediana do RS"
                   if len(sel) < modelos.n else "estado inteiro")
    cartoes = [("Municípios na seleção", f"{len(sel)} de {modelos.n}", None)]
    if pergunta == "P1":
        cartoes += [
            ("Renda mediana dos ocupados", an.reais(renda_sel), delta_renda),
            ("Muito acima do esperado", str((sel["residuo_p1"] > modelos.p1_dp).sum()),
             f"resíduo > {an.reais(modelos.p1_dp)}"),
            ("Muito abaixo do esperado", str((sel["residuo_p1"] < -modelos.p1_dp).sum()),
             f"resíduo < −{an.reais(modelos.p1_dp)}"),
        ]
    elif pergunta == "P2":
        base = sel[["pct_sem_rendimento_2010", "pct_ate_1sm_2010"]].sum(axis=1)
        cartoes += [
            ("Escolaridade mediana", an.formatar(sel[ESCOLARIDADE].median(), 1, sufixo="%"),
             "ocupados com ensino médio"),
            ("Sem rendimento ou até 1 SM", an.formatar(base.mean(), 1, sufixo="%"),
             "média dos municípios"),
            ("Mais de 5 SM", an.formatar(sel["pct_mais_5sm_2010"].mean(), 1, sufixo="%"),
             "média dos municípios"),
        ]
    elif pergunta == "P3":
        # Spearman = Pearson sobre os postos; evita depender do scipy só para isto.
        rho = sel[DISTANCIA].rank().corr(sel[RENDA].rank()) if len(sel) >= 5 else np.nan
        cartoes += [
            ("Renda mediana dos ocupados", an.reais(renda_sel), delta_renda),
            ("Mediana da Metropolitana (RF1)", an.reais(modelos.p3_mediana_rf1), None),
            ("Spearman distância × renda", an.formatar(rho, 2),
             "na seleção (≥ 5 municípios)" if len(sel) >= 5 else "poucos municípios"),
        ]
    else:
        cartoes += [
            ("Ganham muito mais do que produzem", str((sel["residuo_p4"] > modelos.p4_dp).sum()),
             f"resíduo > {an.reais(modelos.p4_dp)}"),
            ("Produzem muito, renda baixa", str((sel["residuo_p4"] < -modelos.p4_dp).sum()),
             f"resíduo < −{an.reais(modelos.p4_dp)}"),
            ("PIB baixo, renda acima do esperado", f"{int(sel['destaque_p4'].sum())} de 13",
             "contorno preto no mapa"),
        ]
    for coluna, (rotulo, valor, delta) in zip(st.columns(len(cartoes)), cartoes):
        coluna.metric(rotulo, valor, delta, delta_color="off", delta_arrow="off", border=True)


indicadores()


# ---------------------------------------------------------------------------
# Mapa (Folium)
# ---------------------------------------------------------------------------
def cores_e_legenda():
    """Cor de cada município no modo atual e itens da legenda."""
    if pergunta in ("P1", "P4"):
        classes = an.CLASSES_P1 if pergunta == "P1" else an.CLASSES_P4
        coluna = "classe_p1" if pergunta == "P1" else "classe_p4"
        # Rampa sequencial na cor base da pergunta, do claro (abaixo do
        # esperado) ao escuro (acima). A escala não tem meio neutro: quem
        # carrega o sinal do resíduo é o rótulo de cada classe, que diz a
        # direção em palavras.
        escala = an.CORES_RESIDUO[pergunta]
        mapa_cor = dict(zip(classes, escala))
        cores = mun[coluna].astype(object).map(mapa_cor)
        dp = modelos.p1_dp if pergunta == "P1" else modelos.p4_dp
        legenda = list(zip(escala, classes))
        titulo = f"Renda observada − esperada (1 dp = {an.reais(dp)})"
    elif pergunta == "P2":
        cores = mun["quartil_esc"].astype(object).map(dict(zip(an.QUARTIS, an.CORES_QUARTIL)))
        lim = modelos.p2_limites
        legenda = [(cor, f"{q}: {an.formatar(lim[i], 1)}% a {an.formatar(lim[i + 1], 1)}%")
                   for i, (q, cor) in enumerate(zip(an.QUARTIS, an.CORES_QUARTIL))]
        titulo = "Ocupados com ensino médio completo (quartis do RS)"
    else:
        cores = mun["quintil_renda"].map(dict(enumerate(an.CORES_QUINTIL)))
        lim = modelos.p3_limites
        legenda = [(cor, f"{an.reais(lim[i])} a {an.reais(lim[i + 1])}")
                   for i, cor in enumerate(an.CORES_QUINTIL)]
        titulo = "Rendimento médio dos ocupados (quintis do RS)"
    cores = cores.where(com_dado, an.COR_SEM_DADO).fillna(an.COR_SEM_DADO)
    legenda.append((an.COR_SEM_DADO, "Sem dado em 2010 (Pinto Bandeira)"))
    return cores, legenda, titulo


def rotulos(tabela):
    """Colunas de texto para o tooltip — os números seguem intactos no DataFrame."""
    t = pd.DataFrame(index=tabela.index)
    t["Município"] = tabela["NM_MUN"]
    t["Região"] = tabela["regiao_funcional"]
    t["COREDE"] = tabela["corede"]
    t["Renda dos ocupados"] = tabela[RENDA].map(an.reais)
    if pergunta == "P1":
        t["Ensino médio"] = tabela[ESCOLARIDADE].map(lambda v: an.formatar(v, 1, sufixo="%"))
        t["Renda esperada"] = tabela["esperado_p1"].map(an.reais)
        t["Diferença"] = tabela["residuo_p1"].map(lambda v: an.reais(v, sinal=True))
    elif pergunta == "P2":
        t["Ensino médio"] = tabela[ESCOLARIDADE].map(lambda v: an.formatar(v, 1, sufixo="%"))
        t["Quartil"] = tabela["quartil_esc"].astype(object).fillna("sem dado")
        for coluna, nome in an.FAIXAS.items():
            t[nome] = tabela[coluna].map(lambda v: an.formatar(v, 1, sufixo="%"))
    elif pergunta == "P3":
        t["Distância da capital"] = tabela[DISTANCIA].map(lambda v: an.formatar(v, 0, sufixo=" km"))
    else:
        t["PIB per capita"] = tabela[PIB].map(an.reais)
        t["Renda esperada"] = tabela["esperado_p4"].map(an.reais)
        t["Diferença"] = tabela["residuo_p4"].map(lambda v: an.reais(v, sinal=True))
        t["População"] = tabela[POPULACAO].map(lambda v: an.formatar(v, 0, sufixo=" hab."))
        setores = tabela[list(an.SETORES)].dropna()
        lider = setores.idxmax(axis=1).reindex(tabela.index).map(an.SETORES)
        t["Setor líder no VAB"] = [
            f"{s} ({an.formatar(p, 0, sufixo='%')})" if isinstance(s, str) else "sem dado"
            for s, p in zip(lider, tabela["pct_setor_lider"])]
    return t


class Enquadrar(MacroElement):
    """fitBounds que se refaz quando o contêiner muda de tamanho.

    O `fit_bounds` do folium roda uma vez, na criação do mapa. Dentro do
    Streamlit a coluna ainda não tem a largura final nesse instante, e o
    Leaflet escolhe o zoom para um contêiner errado: o RS abre pequeno demais
    ou cortado. O ajuste é repetido quando o contêiner muda de tamanho e em
    três momentos após a criação, ignorando os instantes em que ele ainda
    está sem tamanho.
    """

    _template = Template("""
        {% macro script(this, kwargs) %}
        (function (mapa) {
            var limites = {{ this.limites|tojson }};
            function ajustar() {
                var caixa = mapa.getContainer();
                if (!caixa.clientWidth || !caixa.clientHeight) return;  // ainda oculto
                mapa.invalidateSize({animate: false});
                mapa.fitBounds(limites, {padding: [4, 4], animate: false});
            }
            if (window.ResizeObserver) {
                new ResizeObserver(ajustar).observe(mapa.getContainer());
            }
            [100, 500, 1500].forEach(function (ms) { setTimeout(ajustar, ms); });
        })({{ this._parent.get_name() }});
        {% endmacro %}
    """)

    def __init__(self, limites):
        super().__init__()
        self._name = "Enquadrar"
        self.limites = limites


def montar_mapa(cores):
    # Sem mapa-base: os servidores do OpenStreetMap respondem "403 Access blocked"
    # a pedidos sem Referer, e os polígonos já cobrem todo o RS.
    # scroll_wheel_zoom=False: rolar a página com o mouse sobre o mapa não deve
    # mudar o zoom (os botões + e − continuam).
    mapa = folium.Map(tiles=None, control_scale=True, zoom_snap=0.25, scroll_wheel_zoom=False)
    mapa.get_root().header.add_child(folium.Element(
        "<style>.leaflet-container { background: #f4f3ee !important; }</style>"))

    visiveis = mun[selecao]
    fora = mun[~selecao]
    if not fora.empty:
        folium.GeoJson(
            fora[["geometry"]].__geo_interface__, name="Fora da seleção",
            style_function=lambda _: {"fillColor": an.COR_FORA, "color": "white",
                                      "weight": 0.4, "fillOpacity": 1},
            interactive=False,
        ).add_to(mapa)

    camada = rotulos(visiveis)
    camada["cor"] = cores[selecao]
    camada = gpd.GeoDataFrame(camada, geometry=visiveis.geometry, crs=visiveis.crs)
    campos = [c for c in camada.columns if c not in ("cor", "geometry")]
    folium.GeoJson(
        camada.__geo_interface__, name="Municípios",
        # O cinza de "sem dado" recua de propósito para não competir com o
        # passo mais claro da rampa, então ganha um traço escuro: a distinção
        # não pode depender só da cor de preenchimento.
        style_function=lambda f: {
            "fillColor": f["properties"]["cor"], "fillOpacity": 0.92,
            "color": "#8a8a86" if f["properties"]["cor"] == an.COR_SEM_DADO else "white",
            "weight": 1.2 if f["properties"]["cor"] == an.COR_SEM_DADO else 0.4},
        highlight_function=lambda _: {"weight": 2.2, "color": "#1a1a1a"},
        tooltip=folium.GeoJsonTooltip(
            fields=campos, aliases=[f"{c}:" for c in campos], sticky=True,
            style="font: 12px sans-serif; padding: 6px;"),
    ).add_to(mapa)

    folium.GeoJson(
        regioes[["geometry"]].__geo_interface__, name="Regiões Funcionais",
        style_function=lambda _: {"fillOpacity": 0, "color": "#2b2b2b", "weight": 1.3},
        interactive=False,
    ).add_to(mapa)

    if pergunta == "P3":
        # Contorno em tinta neutra, e não colorido: o mapa inteiro já é uma
        # rampa de um matiz, e um contorno com cor competiria com a escala de
        # valor. O que separa as duas regiões é o traço — cheio e tracejado.
        contornos = {1: None, 3: "7 4"}
        for rf_id, tracejado in contornos.items():
            folium.GeoJson(
                regioes.loc[regioes["regiao_funcional_id"] == rf_id, ["geometry"]].__geo_interface__,
                style_function=lambda _, d=tracejado: {
                    "fillOpacity": 0, "color": "#0b0b0b", "weight": 2.6, "dashArray": d},
                interactive=False,
            ).add_to(mapa)
        lat, lon = modelos.centro_poa
        for raio in (100, 200, 300):
            folium.Circle([lat, lon], radius=raio * 1000, color="#52514e", weight=1.2,
                          dash_array="6 5", fill=False, interactive=False).add_to(mapa)
            folium.Marker(
                [lat + raio / 111.2, lon],
                icon=folium.DivIcon(html=(
                    '<div style="font:11px sans-serif;color:#3a3a36;background:#fffc;'
                    f'padding:0 3px;white-space:nowrap;transform:translate(-50%,-50%)">{raio} km</div>')),
            ).add_to(mapa)
        folium.Marker(
            [lat, lon],
            icon=folium.DivIcon(html=(
                '<div style="font:bold 12px sans-serif;color:#0b0b0b;white-space:nowrap;'
                'transform:translate(-8px,-12px)">★ Porto Alegre</div>')),
        ).add_to(mapa)

    if pergunta == "P4":
        destaque = mun[selecao & mun["destaque_p4"]]
        if not destaque.empty:
            folium.GeoJson(
                destaque[["geometry"]].__geo_interface__, name="PIB baixo, renda acima",
                style_function=lambda _: {"fillOpacity": 0, "color": "#0b0b0b", "weight": 2.4},
                interactive=False,
            ).add_to(mapa)

    oeste, sul, leste, norte = visiveis.total_bounds
    Enquadrar([[float(sul), float(oeste)], [float(norte), float(leste)]]).add_to(mapa)
    return mapa


def legenda_html(itens, titulo, extras=()):
    linhas = "".join(
        f'<div style="display:flex;align-items:center;gap:6px;margin:2px 0">'
        f'<span style="width:13px;height:13px;background:{cor};border:1px solid #bbb;'
        f'flex:none"></span>{texto}</div>' for cor, texto in itens)
    linhas += "".join(
        f'<div style="display:flex;align-items:center;gap:6px;margin:2px 0">'
        f'<span style="width:13px;height:0;border-top:{borda};flex:none"></span>{texto}</div>'
        for borda, texto in extras)
    return f'<div style="font-size:0.85rem"><b>{titulo}</b>{linhas}</div>'


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
cores, itens_legenda, titulo_legenda = cores_e_legenda()
extras = [("2px solid #2b2b2b", "Fronteira de Região Funcional")]
if pergunta == "P3":
    # Mesma tinta nas duas: o que as separa é o traço, como no mapa.
    extras += [("2.6px solid #0b0b0b", "RF1 · Metropolitana"),
               ("2.6px dashed #0b0b0b", "RF3 · Serra e Hortênsias"),
               ("1.5px dashed #52514e", "100, 200 e 300 km de Porto Alegre")]
if pergunta == "P4":
    extras += [("2.5px solid #0b0b0b", "Tercil inferior de PIB com renda acima do esperado")]



def secao(titulo, selo, cor, nota=None):
    """Cabeçalho de bloco com o selo que diz de qual atividade ele vem."""
    st.divider()
    st.badge(selo, color=cor)
    st.markdown(f"#### {titulo}")
    if nota:
        st.caption(nota)


def selo_atividade01(numero):
    novidade = " · novidade" if pergunta == "P4" else ""
    return f"Atividade 01 · gráfico {numero}{novidade}"


# Mapa — Atividade 02
secao("Mapa interativo", f"Atividade 02 · {ORIGEM_MAPA[pergunta]}", "green", COMO_LER[pergunta])
# HTML do próprio folium num iframe: o mapa só é lido, não devolve cliques ao
# app, então não é preciso um componente bidirecional como o streamlit-folium.
# O HTML é gerado aqui mesmo, a partir dos dados do projeto.
html_mapa = montar_mapa(cores).get_root().render()
if hasattr(st, "iframe"):
    st.iframe(html_mapa, height=620)
else:  # Streamlit anterior ao st.iframe
    import streamlit.components.v1 as components
    components.html(html_mapa, height=620)
st.markdown(legenda_html(itens_legenda, titulo_legenda, extras), unsafe_allow_html=True)
st.caption("Passe o mouse sobre um município para ver os valores. Em cinza-claro, municípios fora "
           "da seleção.")

# Gráficos — Atividade 01, no mesmo modelo de atividade01_dados_pib_2010.ipynb
NOTA_A01 = ("Mesmo gráfico de `atividade01_dados_pib_2010.ipynb`, redesenhado com os dados do "
            "dashboard. As estatísticas continuam calculadas sobre os 496 municípios; os filtros "
            "só destacam a seleção (em cinza, o que está fora dela).")
# O 6.3.2 usa os mesmos dados do notebook, mas outro desenho: pontos e traço de
# mediana no lugar do boxplot. Os números são os mesmos; o que muda é o que a
# figura mostra de imediato — o n de cada região em vez dos quartis.
NOTA_632 = ("Mesmos dados da seção 6.3.2 de `atividade01_dados_pib_2010.ipynb` — os 496 municípios "
            "com rendimento em 2010 — em outro desenho: cada ponto é um município e o traço "
            "vertical é a mediana da região, no lugar do boxplot do notebook. As medianas e a "
            "ordem das regiões são idênticas; os filtros só destacam a seleção.")
filtrado = len(sel) < modelos.n
if pergunta == "P1":
    secao("6.1 — Escolaridade × rendimento", selo_atividade01("6.1"), "blue", NOTA_A01)
    st.pyplot(g1.grafico_6_1(mun, modelos, selecao), width="content")
elif pergunta == "P2":
    secao("6.2.1 — Faixas de renda por quartil de escolaridade (resposta da pergunta 2)",
          selo_atividade01("6.2.1"), "blue",
          "Versão em quartis descrita no título da seção 6.2.1 e interpretada em 6.2.2 de "
          "`atividade01_versao_final.ipynb`: cada grupo tem cerca de 124 municípios. Os limites dos "
          "quartis são os do estado; com filtro, as barras mostram a média dos municípios da seleção.")
    st.pyplot(g1.grafico_6_2(sel, modelos, filtrado), width="content")
    if filtrado and (an.medias_faixas(sel)[1].between(1, 4)).any():
        st.caption("Atenção: há quartil com menos de 5 municípios na seleção — a média dele é instável.")

elif pergunta == "P3":
    secao("6.3.2 — Renda por Região Funcional", selo_atividade01("6.3.2"), "blue", NOTA_632)
    st.pyplot(g1.grafico_6_3(mun, selecao, rfs), width="content")
else:
    secao("6.4.2 — Quem foge do padrão produção → renda", selo_atividade01("6.4.2"), "blue", NOTA_A01)
    st.pyplot(g1.grafico_6_4_2(mun, modelos, selecao), width="content")
    secao("6.4.3 — O que distingue os de renda alta entre os de PIB baixo", selo_atividade01("6.4.3"),
          "blue", NOTA_A01)
    st.pyplot(g1.grafico_6_4_3(mun, modelos, selecao, p_valores_p4), width="content")


# ---------------------------------------------------------------------------
# Tabela
# ---------------------------------------------------------------------------
secao("Municípios da seleção", "Atividade 02 · novo nesta atividade", "green")
comuns = {"NM_MUN": "Município", "corede": "COREDE", "regiao_funcional": "Região Funcional"}
DINHEIRO = st.column_config.NumberColumn(format="R$ %.0f")
if pergunta == "P1":
    colunas = {**comuns, ESCOLARIDADE: "Ensino médio (%)", RENDA: "Renda (R$)",
               "esperado_p1": "Renda esperada (R$)", "residuo_p1": "Diferença (R$)"}
    ordem, crescente = "residuo_p1", True
    formatos = {"Ensino médio (%)": st.column_config.NumberColumn(format="%.1f"),
                "Renda (R$)": DINHEIRO, "Renda esperada (R$)": DINHEIRO,
                "Diferença (R$)": st.column_config.NumberColumn(format="%+.0f")}
    nota = "Ordenada da maior diferença negativa para a maior positiva — clique no cabeçalho para reordenar."
elif pergunta == "P2":
    colunas = {**comuns, ESCOLARIDADE: "Ensino médio (%)", "quartil_esc": "Quartil",
               **{c: n for c, n in an.FAIXAS.items()}}
    ordem, crescente = ESCOLARIDADE, True
    formatos = {n: st.column_config.NumberColumn(format="%.1f") for n in
                ["Ensino médio (%)", *an.FAIXAS.values()]}
    nota = "Faixas de renda em % dos ocupados do município."
elif pergunta == "P3":
    colunas = {**comuns, RENDA: "Renda (R$)", DISTANCIA: "Distância a Porto Alegre (km)"}
    ordem, crescente = RENDA, False
    formatos = {"Renda (R$)": DINHEIRO,
                "Distância a Porto Alegre (km)": st.column_config.NumberColumn(format="%.0f")}
    nota = "Ordenada da maior para a menor renda."
else:
    colunas = {**comuns, PIB: "PIB per capita (R$)", RENDA: "Renda (R$)", "residuo_p4": "Diferença (R$)",
               POPULACAO: "População", **{c: f"{n} (% VAB)" for c, n in an.SETORES.items()}}
    ordem, crescente = "residuo_p4", False
    formatos = {"PIB per capita (R$)": DINHEIRO, "Renda (R$)": DINHEIRO,
                "Diferença (R$)": st.column_config.NumberColumn(format="%+.0f"),
                "População": st.column_config.NumberColumn(format="%d"),
                **{f"{n} (% VAB)": st.column_config.NumberColumn(format="%.1f") for n in an.SETORES.values()}}
    nota = "Ordenada da maior diferença positiva para a maior negativa."

tabela = pd.DataFrame(sel.sort_values(ordem, ascending=crescente)[list(colunas)]).rename(columns=colunas)
if "Quartil" in tabela:
    tabela["Quartil"] = tabela["Quartil"].astype(str)
st.dataframe(tabela, hide_index=True, height=320, width="stretch", column_config=formatos)
st.caption(nota)


# ---------------------------------------------------------------------------
# Rodapé
# ---------------------------------------------------------------------------
st.divider()
st.caption(FONTES)
st.caption(
    "Limitações: corte único de 2010, sem tendência; a unidade é o município (nada aqui descreve "
    "indivíduos) e cada município pesa 1, independente da população; Pinto Bandeira, emancipado em "
    "2013, não tem dado de 2010; a distância é em linha reta entre centroides, não tempo de "
    "deslocamento.")
