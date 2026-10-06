"""Pergunta 4 — Renda incompatível com a produção local (novidade)."""

import folium
import streamlit as st

import analise as an
import comum
import graficos_atividade01 as g1
from analise import PIB, POPULACAO, RENDA

NOVIDADE = (
    "**Novidade.** Esta pergunta não estava entre as três perguntas da proposta original da "
    "Atividade 01. Ela foi acrescentada com um terceiro "
    "conjunto de dados — o **PIB dos municípios de 2010 (IBGE)**, que traz PIB per capita, "
    "população e valor adicionado por setor — e é a única que cruza a renda dos moradores com a "
    "produção local.")

ctx = comum.contexto()
m = ctx.modelos

comum.cabecalho(4, "Existem municípios cuja renda dos residentes é incompatível com sua produção "
                   "local, e o que os distingue dos demais de PIB igualmente baixo?", NOVIDADE)

# Controle próprio desta página: restringe a seleção (e por isso vem antes dos cartões).
so_tercil = st.toggle(
    "Só o tercil inferior de PIB per capita", key="so_tercil",
    help=f"Os 166 municípios com PIB per capita até {an.reais(m.p4_corte_tercil)}/hab. — o "
         "recorte da 2ª metade da pergunta.")
selecao = ctx.selecao
if so_tercil:
    selecao &= ctx.mun["tercil_inferior_pib"]
sel = ctx.mun[selecao & ctx.com_dado]
comum.parar_se_vazio(ctx, sel, "ou desligue o recorte do tercil inferior de PIB")

comum.cartoes(ctx, sel, [
    ("Muito acima do esperado", str((sel["residuo_p4"] > m.p4_dp).sum()),
     f"resíduo > {an.reais(m.p4_dp)}"),
    ("Muito abaixo do esperado", str((sel["residuo_p4"] < -m.p4_dp).sum()),
     f"resíduo < −{an.reais(m.p4_dp)}"),
    ("PIB baixo, renda alta", f"{int(sel['destaque_p4'].sum())} de 13",
     "contorno no mapa"),
])

escala = an.CORES_RESIDUO["P4"]
cores = ctx.mun["classe_p4"].astype(object).map(dict(zip(an.CLASSES_P4, escala)))

visiveis = ctx.mun[selecao]
tooltip = comum.tooltip_base(visiveis)
tooltip["PIB per capita"] = visiveis[PIB].map(an.reais)
tooltip["Renda esperada"] = visiveis["esperado_p4"].map(an.reais)
tooltip["Diferença"] = visiveis["residuo_p4"].map(lambda v: an.reais(v, sinal=True))
tooltip["População"] = visiveis[POPULACAO].map(lambda v: an.formatar(v, 0, sufixo=" hab."))
setores = visiveis[list(an.SETORES)].dropna()
lider = setores.idxmax(axis=1).reindex(visiveis.index).map(an.SETORES)
tooltip["Setor líder no VAB"] = [
    f"{s} ({an.formatar(p, 0, sufixo='%')})" if isinstance(s, str) else "sem dado"
    for s, p in zip(lider, visiveis["pct_setor_lider"])]


def contorno_destaque(mapa):
    destaque = ctx.mun[selecao & ctx.mun["destaque_p4"]]
    if not destaque.empty:
        folium.GeoJson(
            destaque[["geometry"]].__geo_interface__, name="PIB baixo, renda acima",
            style_function=lambda _: {"fillOpacity": 0, "color": "#0b0b0b", "weight": 2.4},
            interactive=False,
        ).add_to(mapa)


comum.secao_mapa(
    ctx, selecao, cores, list(zip(escala, an.CLASSES_P4)),
    f"Renda observada − esperada (1 dp = {an.reais(m.p4_dp)})", tooltip,
    origem="novo nesta atividade",
    como_ler=("O mapa mostra quanto a renda se afasta da **renda esperada pelo PIB per capita**. "
              "Quanto mais escuro, mais a renda supera o que o PIB per capita faria esperar; os "
              "tons claros produzem muito e a renda não fica com os residentes. Contorno preto: os "
              "municípios do tercil inferior de PIB com renda acima do esperado."),
    extras_legenda=[("2.5px solid #0b0b0b", "Tercil inferior de PIB com renda acima do esperado")],
    camadas_extras=contorno_destaque)

# comum.secao("Quem foge do padrão produção → renda",
#             comum.selo_atividade01(novidade=True), "blue", comum.NOTA_A01)
# st.pyplot(g1.grafico_pib_renda(ctx.mun, m, selecao), width="content")

# comum.secao("O que distingue os de renda alta entre os de PIB baixo",
#             comum.selo_atividade01(novidade=True), "blue", comum.NOTA_A01)
# st.pyplot(g1.grafico_tercil_inferior(ctx.mun, m, selecao, ctx.p_valores_p4), width="content")

comum.tabela(
    sel,
    {PIB: "PIB per capita (R$)", RENDA: "Renda (R$)", "residuo_p4": "Diferença (R$)",
     POPULACAO: "População", **{c: f"{n} (% VAB)" for c, n in an.SETORES.items()}},
    ordem="residuo_p4", crescente=False,
    formatos={"PIB per capita (R$)": comum.DINHEIRO, "Renda (R$)": comum.DINHEIRO,
              "Diferença (R$)": st.column_config.NumberColumn(format="%+.0f"),
              "População": st.column_config.NumberColumn(format="%d"),
              **{f"{n} (% VAB)": st.column_config.NumberColumn(format="%.1f")
                 for n in an.SETORES.values()}},
    nota="Ordenada da maior diferença positiva para a maior negativa.")

comum.rodape()
