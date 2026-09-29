"""Pergunta 3 — A proximidade da capital explica o rendimento dos ocupados?"""

import folium
import numpy as np
import streamlit as st

import analise as an
import comum
import graficos_atividade01 as g1
from analise import DISTANCIA, RENDA

ctx = comum.contexto()
m = ctx.modelos
selecao = ctx.selecao
sel = ctx.mun[selecao & ctx.com_dado]

comum.cabecalho(3, "A proximidade da capital explica o rendimento médio dos ocupados, ou há "
                   "regiões não metropolitanas com rendimento equivalente ou superior?")
comum.parar_se_vazio(ctx, sel)

# Spearman = Pearson sobre os postos; evita depender do scipy só para isto.
rho = sel[DISTANCIA].rank().corr(sel[RENDA].rank()) if len(sel) >= 5 else np.nan
comum.cartoes(ctx, sel, [
    ("Renda mediana dos ocupados", an.reais(sel[RENDA].median()), comum.delta_renda(ctx, sel)),
    ("Mediana da Metropolitana (RF1)", an.reais(m.p3_mediana_rf1), None),
    ("Spearman distância × renda", an.formatar(rho, 2),
     "na seleção" if len(sel) >= 5 else "menos de 5 municípios"),
])

cores = ctx.mun["quintil_renda"].map(dict(enumerate(an.CORES_QUINTIL)))
lim = m.p3_limites
legenda = [(cor, f"{an.reais(lim[i])} a {an.reais(lim[i + 1])}")
           for i, cor in enumerate(an.CORES_QUINTIL)]

visiveis = ctx.mun[selecao]
tooltip = comum.tooltip_base(visiveis)
tooltip["Distância da capital"] = visiveis[DISTANCIA].map(lambda v: an.formatar(v, 0, sufixo=" km"))


def aneis_e_contornos(mapa):
    # Contorno em tinta neutra, e não colorido: o mapa inteiro já é uma rampa de
    # um matiz, e um contorno com cor competiria com a escala de valor. O que
    # separa as duas regiões é o traço — cheio e tracejado.
    # Cada contorno tem um traço branco por baixo ("casing"): o tom mais escuro da
    # rampa é quase preto, e sem ele a linha preta sumiria sobre esses municípios.
    for rf_id, tracejado in {1: None, 3: "7 4"}.items():
        contorno = ctx.regioes.loc[ctx.regioes["regiao_funcional_id"] == rf_id, ["geometry"]]
        for estilo in ({"color": "#ffffff", "weight": 5.2, "dashArray": None},
                       {"color": "#0b0b0b", "weight": 2.4, "dashArray": tracejado}):
            folium.GeoJson(
                contorno.__geo_interface__,
                style_function=lambda _, e=estilo: {"fillOpacity": 0, **e},
                interactive=False,
            ).add_to(mapa)
    lat, lon = m.centro_poa
    for raio in (100, 200, 300):
        # Anéis com o mesmo "casing" dos contornos das regiões, e pelo mesmo
        # motivo: um traço de cor única cruza os cinco passos da rampa e some em
        # algum deles. Um cinza médio chegava a 1,07:1 contra o passo do meio —
        # invisível. Com o par claro/escuro, o escuro carrega a linha sobre os
        # tons claros e o claro a carrega sobre os escuros.
        for estilo in ({"color": "#ffffff", "weight": 3.2, "opacity": 0.9},
                       {"color": "#1a1a1a", "weight": 1.3, "opacity": 1}):
            folium.Circle([lat, lon], radius=raio * 1000, dash_array="3 6",
                          fill=False, interactive=False, **estilo).add_to(mapa)
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
            'text-shadow:0 0 3px #fff,0 0 3px #fff,0 0 3px #fff;'
            'transform:translate(-8px,-12px)">★ Porto Alegre</div>')),
    ).add_to(mapa)


comum.secao_mapa(
    ctx, selecao, cores, legenda, "Rendimento médio dos ocupados (quintis do RS)", tooltip,
    origem="novo nesta atividade",
    como_ler=("O mapa pinta a **renda em quintis**. Os anéis marcam 100, 200 e 300 km de Porto "
              "Alegre: se a proximidade explicasse a renda, os tons escuros se concentrariam no "
              "centro. Contornos: Metropolitana (traço cheio) e Serra e Hortênsias (tracejado)."),
    # Mesma tinta nas duas regiões: o que as separa é o traço, como no mapa.
    extras_legenda=[("2.6px solid #0b0b0b", "RF1 · Metropolitana"),
                    ("2.6px dashed #0b0b0b", "RF3 · Serra e Hortênsias"),
                    ("1.5px dashed #1a1a1a", "100, 200 e 300 km de Porto Alegre")],
    camadas_extras=aneis_e_contornos,
    # Nesta página as fronteiras das 9 regiões recuam para um cinza fino: o que
    # a pergunta compara é a RF1 e a RF3, que ganham o contorno preto.
    fronteira={"color": "#9a9994", "weight": 0.8})

# Mesmos dados da Atividade 01, outro desenho: pontos e traço de mediana no
# lugar do boxplot. Os números são os mesmos; o que muda é o que a figura
# mostra de imediato — o n de cada região em vez dos quartis.
comum.secao(
    "Renda por Região Funcional", comum.selo_atividade01(), "blue",
    "Mesmos dados da Atividade 01 — os 496 municípios com rendimento em 2010 — em outro "
    "desenho: cada ponto é um município e o traço vertical é a mediana da região, no lugar do "
    "boxplot original. As medianas e a ordem das regiões são idênticas; os filtros só destacam "
    "a seleção.")
st.pyplot(g1.grafico_renda_por_regiao(ctx.mun, selecao, ctx.rfs), width="content")

comum.tabela(
    sel, {RENDA: "Renda (R$)", DISTANCIA: "Distância a Porto Alegre (km)"},
    ordem=RENDA, crescente=False,
    formatos={"Renda (R$)": comum.DINHEIRO,
              "Distância a Porto Alegre (km)": st.column_config.NumberColumn(format="%.0f")},
    nota="Ordenada da maior para a menor renda.")

comum.rodape()
