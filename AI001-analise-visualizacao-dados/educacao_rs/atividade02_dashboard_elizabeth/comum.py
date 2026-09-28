"""Peças que todas as páginas do dashboard compartilham.

Cada página (pasta `paginas/`) monta a sua pergunta com estas funções: lê os
dados e os filtros com `contexto()`, desenha os cartões, o mapa e a tabela, e
fecha com o rodapé. O que é específico de uma pergunta — cores do mapa, colunas
do tooltip, gráficos da Atividade 01, controles próprios — fica na página.
"""

from dataclasses import dataclass

import folium
import geopandas as gpd
import pandas as pd
import streamlit as st
from branca.element import MacroElement
from jinja2 import Template

import analise as an
from analise import RENDA

FONTES = ("Fontes: Atlas do Desenvolvimento Humano no Brasil (Pnud, Ipea, FJP), Censo 2010 (IBGE); "
          "PIB dos municípios 2010 (IBGE); malha municipal 2022 (IBGE); Regiões Funcionais e "
          "COREDEs — Decreto 54.572/2019 (SEPLAG-RS).")
LIMITACOES = (
    "Limitações: corte único de 2010, sem tendência; a unidade é o município (nada aqui descreve "
    "indivíduos) e cada município pesa 1, independente da população; Pinto Bandeira, emancipado em "
    "2013, não tem dado de 2010; a distância é em linha reta entre centroides, não tempo de "
    "deslocamento.")
NOTA_A01 = ("Mesmo gráfico de `atividade01_dados_pib_2010.ipynb`, redesenhado com os dados do "
            "dashboard. As estatísticas continuam calculadas sobre os 496 municípios; os filtros "
            "só destacam a seleção (em cinza, o que está fora dela).")
DINHEIRO = st.column_config.NumberColumn(format="R$ %.0f")


# ---------------------------------------------------------------------------
# Dados e filtros
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Carregando os municípios…")
def carregar():
    municipios, regioes = an.carregar()
    municipios, modelos = an.calcular(municipios)
    return municipios, regioes, modelos, an.testes_p4(municipios)


@dataclass
class Contexto:
    """Dados carregados + filtros comuns da barra lateral."""

    mun: pd.DataFrame
    regioes: gpd.GeoDataFrame
    modelos: an.Modelos
    p_valores_p4: dict
    rfs: list
    coredes: list

    @property
    def com_dado(self):
        return self.mun[RENDA].notna()

    @property
    def selecao(self):
        """Máscara dos municípios que passam nos filtros de região e COREDE."""
        s = self.mun["regiao_funcional"].isin(self.rfs)
        if self.coredes:
            s &= self.mun["corede"].isin(self.coredes)
        return s


def todas_rf(mun):
    return sorted(mun["regiao_funcional"].unique(), key=lambda n: int(n[2:n.index(" ")]))


def contexto():
    """Dados e filtros comuns. Os filtros são desenhados em app.py (chaves rfs e coredes)."""
    mun, regioes, modelos, p_valores_p4 = carregar()
    return Contexto(mun, regioes, modelos, p_valores_p4,
                    rfs=st.session_state.get("rfs", todas_rf(mun)),
                    coredes=st.session_state.get("coredes", []))


# ---------------------------------------------------------------------------
# Cabeçalho, avisos e rodapé
# ---------------------------------------------------------------------------
def cabecalho(numero, enunciado, novidade=None):
    st.caption(f"Pergunta {numero} de 4 · Censo 2010 · municípios do RS")
    st.header(enunciado)
    if novidade:
        st.info(novidade, icon="✨")


def parar_se_vazio(ctx, sel, dica=""):
    if not ctx.rfs:
        st.info("Nenhuma Região Funcional selecionada. Escolha ao menos uma na barra lateral.")
        st.stop()
    if sel.empty:
        st.info("A combinação de filtros não deixou nenhum município com dado. "
                "Amplie a seleção de regiões ou de COREDEs" + (f", {dica}" if dica else "") + ".")
        st.stop()


def rodape():
    st.divider()
    st.caption(FONTES)
    st.caption(LIMITACOES)


def secao(titulo, selo, cor, nota=None):
    """Cabeçalho de bloco com o selo que diz de qual atividade ele vem."""
    st.divider()
    st.badge(selo, color=cor)
    st.markdown(f"#### {titulo}")
    if nota:
        st.caption(nota)


def selo_atividade01(numero, novidade=False):
    return f"Atividade 01 · gráfico {numero}" + (" · novidade" if novidade else "")


# ---------------------------------------------------------------------------
# Cartões
# ---------------------------------------------------------------------------
def delta_renda(ctx, sel):
    """Texto da etiqueta do cartão de renda mediana."""
    renda_sel, renda_rs = sel[RENDA].median(), ctx.mun.loc[ctx.com_dado, RENDA].median()
    if len(sel) < ctx.modelos.n:
        return f"{an.reais(renda_sel - renda_rs, sinal=True)} vs. RS"
    return "estado inteiro"


def cartoes(ctx, sel, extras):
    """Primeiro cartão (municípios na seleção) + os cartões da pergunta.

    `extras` é uma lista de (rótulo, valor, etiqueta).
    """
    n_rf, n_corede = sel["regiao_funcional"].nunique(), sel["corede"].nunique()
    if len(sel) < ctx.modelos.n:
        # Curto de propósito: a etiqueta do cartão corta o texto a partir de ~20 caracteres.
        delta_mun = f"{n_rf} RF · {n_corede} COREDE{'' if n_corede == 1 else 's'}"
    else:
        delta_mun = f"todas as {n_rf} regiões"
    lista = [("Municípios na seleção", f"{len(sel)} de {ctx.modelos.n}", delta_mun), *extras]
    for coluna, (rotulo, valor, delta) in zip(st.columns(len(lista)), lista):
        coluna.metric(rotulo, valor, delta, delta_color="off", delta_arrow="off", border=True,
                      height="stretch")


# ---------------------------------------------------------------------------
# Mapa (Folium)
# ---------------------------------------------------------------------------
def tooltip_base(tabela):
    """Colunas de texto comuns ao tooltip de todas as perguntas."""
    t = pd.DataFrame(index=tabela.index)
    t["Município"] = tabela["NM_MUN"]
    t["Região"] = tabela["regiao_funcional"]
    t["COREDE"] = tabela["corede"]
    t["Renda dos ocupados"] = tabela[RENDA].map(an.reais)
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


FRONTEIRA_PADRAO = {"color": "#2b2b2b", "weight": 1.3}


def montar_mapa(ctx, selecao, cores, tooltip, camadas_extras=None, fronteira=FRONTEIRA_PADRAO):
    """Mapa dos municípios.

    `cores`: cor de cada município (Series alinhada a ctx.mun).
    `tooltip`: DataFrame de texto dos municípios da seleção (ver tooltip_base).
    `camadas_extras`: função opcional que recebe o mapa e desenha por cima
    (anéis de distância, contornos de destaque...).
    `fronteira`: cor e espessura das fronteiras das 9 Regiões Funcionais.
    """
    mun = ctx.mun
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

    camada = tooltip.copy()
    camada["cor"] = cores[selecao]
    camada = gpd.GeoDataFrame(camada, geometry=visiveis.geometry, crs=visiveis.crs)
    campos = [c for c in camada.columns if c not in ("cor", "geometry")]
    folium.GeoJson(
        camada.__geo_interface__, name="Municípios",
        # O cinza de "sem dado" recua de propósito para não competir com o
        # passo mais claro da rampa, então ganha um traço escuro: a distinção
        # não pode depender só da cor de preenchimento.
        style_function=lambda f: {
            # Opacidade 1: com transparência, o fundo clareia todos os tons e
            # aproxima os passos da rampa.
            "fillColor": f["properties"]["cor"], "fillOpacity": 1,
            "color": "#8a8a86" if f["properties"]["cor"] == an.COR_SEM_DADO else "white",
            "weight": 1.2 if f["properties"]["cor"] == an.COR_SEM_DADO else 0.4},
        highlight_function=lambda _: {"weight": 2.2, "color": "#1a1a1a"},
        tooltip=folium.GeoJsonTooltip(
            fields=campos, aliases=[f"{c}:" for c in campos], sticky=True,
            style="font: 12px sans-serif; padding: 6px;"),
    ).add_to(mapa)

    folium.GeoJson(
        ctx.regioes[["geometry"]].__geo_interface__, name="Regiões Funcionais",
        style_function=lambda _: {"fillOpacity": 0, **fronteira},
        interactive=False,
    ).add_to(mapa)

    if camadas_extras:
        camadas_extras(mapa)

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


def secao_mapa(ctx, selecao, cores, legenda, titulo_legenda, tooltip, origem, como_ler,
               extras_legenda=(), camadas_extras=None, fronteira=FRONTEIRA_PADRAO):
    """Bloco completo do mapa: selo, texto de leitura, mapa e legenda."""
    cores = cores.where(ctx.com_dado, an.COR_SEM_DADO).fillna(an.COR_SEM_DADO)
    legenda = [*legenda, (an.COR_SEM_DADO, "Sem dado em 2010 (Pinto Bandeira)")]
    extras = [(f"{max(fronteira['weight'], 1.5)}px solid {fronteira['color']}",
               "Fronteira de Região Funcional"), *extras_legenda]

    secao("Mapa interativo", f"Atividade 02 · {origem}", "green", como_ler)
    # HTML do próprio folium num iframe: o mapa só é lido, não devolve cliques ao
    # app, então não é preciso um componente bidirecional como o streamlit-folium.
    html_mapa = montar_mapa(ctx, selecao, cores, tooltip, camadas_extras, fronteira).get_root().render()
    if hasattr(st, "iframe"):
        st.iframe(html_mapa, height=620)
    else:  # Streamlit anterior ao st.iframe
        import streamlit.components.v1 as components
        components.html(html_mapa, height=620)
    st.markdown(legenda_html(legenda, titulo_legenda, extras), unsafe_allow_html=True)
    st.caption("Passe o mouse sobre um município para ver os valores. Em cinza-claro, municípios "
               "fora da seleção.")


# ---------------------------------------------------------------------------
# Tabela
# ---------------------------------------------------------------------------
def tabela(sel, colunas, ordem, crescente, formatos, nota, como_texto=()):
    """Tabela dos municípios da seleção.

    `colunas`: {coluna do DataFrame: título}. `como_texto`: títulos de colunas
    categóricas que precisam virar texto para o st.dataframe.
    """
    secao("Municípios da seleção", "Atividade 02 · novo nesta atividade", "green")
    comuns = {"NM_MUN": "Município", "corede": "COREDE", "regiao_funcional": "Região Funcional"}
    colunas = {**comuns, **colunas}
    t = pd.DataFrame(sel.sort_values(ordem, ascending=crescente)[list(colunas)]).rename(columns=colunas)
    for nome in como_texto:
        t[nome] = t[nome].astype(str)
    st.dataframe(t, hide_index=True, height=320, width="stretch", column_config=formatos)
    st.caption(nota)
