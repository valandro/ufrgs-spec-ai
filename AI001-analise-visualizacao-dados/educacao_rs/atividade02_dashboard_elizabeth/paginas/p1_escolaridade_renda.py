"""Pergunta 1 — Municípios onde mais ocupados têm ensino médio completo pagam melhor?"""

import streamlit as st

import analise as an
import comum
import graficos_atividade01 as g1
from analise import ESCOLARIDADE, RENDA

ctx = comum.contexto()
m = ctx.modelos
selecao = ctx.selecao
sel = ctx.mun[selecao & ctx.com_dado]

comum.cabecalho(1, "Municípios onde mais ocupados têm ensino médio completo pagam melhor?")
comum.parar_se_vazio(ctx, sel)

comum.cartoes(ctx, sel, [
    ("Renda mediana dos ocupados", an.reais(sel[RENDA].median()), comum.delta_renda(ctx, sel)),
    ("Muito acima do esperado", str((sel["residuo_p1"] > m.p1_dp).sum()),
     f"resíduo > {an.reais(m.p1_dp)}"),
    ("Muito abaixo do esperado", str((sel["residuo_p1"] < -m.p1_dp).sum()),
     f"resíduo < −{an.reais(m.p1_dp)}"),
])

# Mapa: resíduo em relação à escolaridade, numa rampa sequencial na cor base da
# pergunta, do claro (abaixo do esperado) ao escuro (acima). A escala não tem
# meio neutro: quem carrega o sinal do resíduo é o rótulo de cada classe.
escala = an.CORES_RESIDUO["P1"]
cores = ctx.mun["classe_p1"].astype(object).map(dict(zip(an.CLASSES_P1, escala)))

visiveis = ctx.mun[selecao]
tooltip = comum.tooltip_base(visiveis)
tooltip["Ensino médio"] = visiveis[ESCOLARIDADE].map(lambda v: an.formatar(v, 1, sufixo="%"))
tooltip["Renda esperada"] = visiveis["esperado_p1"].map(an.reais)
tooltip["Diferença"] = visiveis["residuo_p1"].map(lambda v: an.reais(v, sinal=True))

comum.secao_mapa(
    ctx, selecao, cores, list(zip(escala, an.CLASSES_P1)),
    f"Renda observada − esperada (1 dp = {an.reais(m.p1_dp)})", tooltip,
    origem="Novo nesta atividade",
    como_ler=("O mapa mostra quanto a renda de cada município se afasta da **renda esperada pela "
              "escolaridade** (a reta do gráfico 6.1). Quanto mais escuro, mais o município paga "
              "acima do que a escolaridade sugere; os tons claros ganham menos do que o esperado. "
              "As duas pontas passam de 1 desvio-padrão — são os casos a investigar dentro de cada "
              "COREDE."))

comum.secao("6.1 — Escolaridade × rendimento", comum.selo_atividade01("6.1"), "blue", comum.NOTA_A01)
st.pyplot(g1.grafico_6_1(ctx.mun, m, selecao), width="content")

comum.tabela(
    sel,
    {ESCOLARIDADE: "Ensino médio (%)", RENDA: "Renda (R$)",
     "esperado_p1": "Renda esperada (R$)", "residuo_p1": "Diferença (R$)"},
    ordem="residuo_p1", crescente=True,
    formatos={"Ensino médio (%)": st.column_config.NumberColumn(format="%.1f"),
              "Renda (R$)": comum.DINHEIRO, "Renda esperada (R$)": comum.DINHEIRO,
              "Diferença (R$)": st.column_config.NumberColumn(format="%+.0f")},
    nota="Ordenada da maior diferença negativa para a maior positiva — clique no cabeçalho para reordenar.")

comum.rodape()
