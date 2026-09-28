"""Pergunta 1 — Municípios onde mais ocupados têm ensino médio completo pagam melhor?"""

import streamlit as st

import analise as an
import comum
import graficos_interativos as gi
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

# ---------------------------------------------------------------------------
# Dispersão escolaridade × rendimento — versão interativa
#
# Vem do dashboard de `educacao/tarefa_02` e substitui a figura estática que
# esta página trazia, e abre a página. Os dois filtros abaixo são dele e valem
# só para este gráfico: o mapa, os cartões e a tabela seguem a barra lateral.
# ---------------------------------------------------------------------------
comum.secao("Escolaridade × rendimento", "Atividade 02" " · versão interativa", "green",
            "Cada ponto é um município: o eixo horizontal é o % de ocupados com ensino médio "
            "completo, o vertical é o rendimento médio dos ocupados. A reta é a tendência do "
            "estado inteiro — a mesma que o mapa abaixo usa como referência —, então ela não se "
            "move quando você filtra. Porto Alegre aparece destacada quando está na seleção.")

coluna_faixas, coluna_escolaridade = st.columns([1.3, 1], gap="large")
faixas_sm = coluna_faixas.multiselect(
    "Faixas de renda do município", an.FAIXAS_RENDA_SM, default=an.FAIXAS_RENDA_SM,
    key="faixas_sm_p1",
    help="A faixa é a da renda MÉDIA do município, em múltiplos do salário mínimo de 2010. "
         "Vale só para este gráfico.")

limites = (round(float(ctx.mun[ESCOLARIDADE].min()), 2),
           round(float(ctx.mun[ESCOLARIDADE].max()), 2))
intervalo = coluna_escolaridade.slider(
    "Ocupados com ensino médio completo (%)", *limites, value=limites, step=0.01,
    key="escolaridade_p1", help="Recorta a faixa de escolaridade mostrada no gráfico.")

grafico = sel[sel[ESCOLARIDADE].between(*intervalo)]
if faixas_sm:
    grafico = grafico[grafico[RENDA].map(an.faixa_renda_sm).isin(faixas_sm)]
else:
    grafico = grafico.iloc[:0]

if grafico.empty:
    st.warning("Nenhum município da seleção está nessa combinação de faixa de renda e "
               "escolaridade. Amplie um dos dois controles acima.")
else:
    st.altair_chart(
        gi.dispersao_escolaridade_renda(grafico, m, destacar_poa=True), width="stretch")
    st.caption(
        f"{len(grafico)} de {len(sel)} municípios da seleção. Faixas de renda calculadas sobre o "
        "salário mínimo de 2010, R$ 510,00 (CONSTANZI, Rogério Nagamine; FIPE, 2023). "
        "Passe o mouse sobre um ponto para ver município, COREDE, região e valores.")

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
              "escolaridade** (a reta do gráfico acima). Quanto mais escuro, mais o município paga "
              "acima do que a escolaridade sugere; os tons claros ganham menos do que o esperado. "
              "As duas pontas passam de 1 desvio-padrão — são os casos a investigar dentro de cada "
              "COREDE."))

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
