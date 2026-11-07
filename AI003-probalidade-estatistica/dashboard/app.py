"""Painéis 1 e 2 — Análise descritiva da população e da amostra (Streamlit).

Eleições 2026, Porto Alegre, Presidente: seções eleitorais, 1º e 2º turnos (fonte: TSE, boletins de urna).
Executar:  streamlit run dashboard/app.py
"""
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DADOS = Path(__file__).resolve().parent / "dados"
COR_LULA, COR_FLAVIO, COR_POP, COR_AMO = "#C0392B", "#1F4E9C", "#6C7A89", "#E08E0B"
CORES_CAND = {"LULA": COR_LULA, "FLAVIO BOLSONARO": COR_FLAVIO, "FLAVIO": COR_FLAVIO}

QUANTI = {
    "PCT_LULA_1t": "% Lula — 1º turno (votos válidos)",
    "PCT_LULA_2t": "% Lula — 2º turno (votos válidos)",
    "DELTA_LULA_PP": "Variação do % de Lula (2º − 1º, p.p.) — votos válidos",
    "PCT_LULA_TOTAL_1t": "% Lula — 1º turno (votos totais, com brancos e nulos)",
    "PCT_LULA_TOTAL_2t": "% Lula — 2º turno (votos totais, com brancos e nulos)",
    "DELTA_LULA_TOTAL_PP": "Variação do % de Lula (2º − 1º, p.p.) — votos totais",
    "PCT_BRANCO_NULO_1t": "% de brancos e nulos — 1º turno (votos totais)",
    "PCT_BRANCO_NULO_2t": "% de brancos e nulos — 2º turno (votos totais)",
    "PCT_ABSTENCAO_1t": "% de abstenção — 1º turno",
    "PCT_ABSTENCAO_2t": "% de abstenção — 2º turno",
    "QT_APTOS_1t": "Eleitores aptos por seção",
}
QUALI = {
    "VENCEDOR_1t": "Vencedor da seção — 1º turno",
    "VENCEDOR_2t": "Vencedor da seção — 2º turno",
    "MUDOU_VENCEDOR": "Mudou de vencedor entre os turnos?",
    "TRAJETORIA": "Trajetória (1º → 2º turno)",
    "NR_ZONA": "Zona eleitoral",
}

st.set_page_config(page_title="Eleições 2026 — Porto Alegre", page_icon="🗳️", layout="wide")


@st.cache_data
def carrega(nome):
    df = pd.read_csv(DADOS / nome)
    df["NR_ZONA"] = df["NR_ZONA"].astype(str)
    return df


def descritivas(df, cols):
    r = pd.DataFrame({
        "n": df[cols].count(), "média": df[cols].mean(), "mediana": df[cols].median(),
        "desvio-padrão": df[cols].std(), "CV (%)": df[cols].std() / df[cols].mean().abs() * 100,
        "mínimo": df[cols].min(), "Q1": df[cols].quantile(.25), "Q3": df[cols].quantile(.75),
        "máximo": df[cols].max(), "assimetria": df[cols].skew(),
    })
    r.index = [QUANTI[c] for c in cols]
    return r


def frequencias(df, col):
    f = df[col].value_counts().sort_index()
    return pd.DataFrame({"categoria": f.index, "frequência": f.values, "proporção (%)": f.values / f.sum() * 100})


def kpis(df):
    c = st.columns(3)
    c[0].metric("Seções", f"{len(df):,}".replace(",", "."))
    c[1].metric("Eleitores aptos", f"{int(df.QT_APTOS_1t.sum()):,}".replace(",", "."))
    c[2].metric("Mudaram de vencedor", f"{(df.MUDOU_VENCEDOR == 'Sim').mean():.1%}")
    c = st.columns(3)
    c[0].metric("Seções de Lula — 1º turno", f"{(df.VENCEDOR_1t == 'LULA').mean():.1%}")
    c[1].metric("Seções de Lula — 2º turno", f"{(df.VENCEDOR_2t == 'LULA').mean():.1%}")
    c[2].metric("Abstenção média (1º → 2º)", f"{df.PCT_ABSTENCAO_1t.mean():.1f}% → {df.PCT_ABSTENCAO_2t.mean():.1f}%")


def painel_descritivo(df, cor, rotulo):
    kpis(df)
    st.divider()

    st.subheader("Variáveis quantitativas")
    var = st.selectbox("Variável", list(QUANTI), format_func=QUANTI.get, key=f"q_{rotulo}")
    g1, g2 = st.columns([3, 2])
    with g1:
        fig = px.histogram(df, x=var, nbins=30, color_discrete_sequence=[cor], marginal="box",
                           labels={var: QUANTI[var]})
        fig.add_vline(x=df[var].mean(), line_dash="dash", annotation_text="média")
        fig.update_layout(height=420, margin=dict(t=20), yaxis_title="nº de seções")
        st.plotly_chart(fig, width="stretch")
    with g2:
        st.markdown("**Medidas descritivas**")
        st.dataframe(descritivas(df, [var]).T.style.format("{:.2f}"), width="stretch")
        st.caption("CV = desvio-padrão / média. Assimetria > 0: cauda à direita.")
    with st.expander("Medidas descritivas de todas as variáveis quantitativas"):
        st.dataframe(descritivas(df, list(QUANTI)).style.format("{:.2f}"), width="stretch")

    st.subheader("Variáveis qualitativas")
    cat = st.selectbox("Variável", list(QUALI), format_func=QUALI.get, key=f"c_{rotulo}")
    f = frequencias(df, cat)
    g1, g2 = st.columns([3, 2])
    with g1:
        fig = px.bar(f, x="categoria", y="frequência", text=f["proporção (%)"].map("{:.1f}%".format),
                     color="categoria", color_discrete_map=CORES_CAND, color_discrete_sequence=[cor])
        fig.update_layout(height=380, showlegend=False, margin=dict(t=20), xaxis_title=QUALI[cat],
                          yaxis_title="nº de seções")
        st.plotly_chart(fig, width="stretch")
    with g2:
        st.markdown("**Frequências e proporções**")
        st.dataframe(f.style.format({"proporção (%)": "{:.2f}"}), width="stretch", hide_index=True)

    st.subheader("Composição dos votos (média das seções)")
    st.caption("Votos totais = válidos + brancos + nulos (igual ao comparecimento). No 2º turno só há dois candidatos.")
    comp = []
    for t, nome in (("1t", "1º turno"), ("2t", "2º turno")):
        lula, flavio, bn = (df[f"PCT_LULA_TOTAL_{t}"].mean(), df[f"PCT_FLAVIO_TOTAL_{t}"].mean(),
                            df[f"PCT_BRANCO_NULO_{t}"].mean())
        comp += [(nome, "Lula", lula), (nome, "Flávio Bolsonaro", flavio),
                 (nome, "Outros candidatos", 100 - lula - flavio - bn), (nome, "Brancos e nulos", bn)]
    comp = pd.DataFrame(comp, columns=["turno", "grupo", "%"])
    g1, g2 = st.columns([3, 2])
    with g1:
        fig = px.bar(comp, x="%", y="turno", color="grupo", orientation="h", barmode="stack",
                     text=comp["%"].map(lambda v: f"{v:.1f}%" if v >= 1 else ""),
                     color_discrete_map={"Lula": COR_LULA, "Flávio Bolsonaro": COR_FLAVIO,
                                         "Outros candidatos": "#9AA5B1", "Brancos e nulos": "#2E2E2E"})
        fig.update_layout(height=260, margin=dict(t=20), yaxis_title=None, xaxis_title="% dos votos totais")
        st.plotly_chart(fig, width="stretch")
    with g2:
        st.dataframe(comp.pivot(index="grupo", columns="turno", values="%").style.format("{:.2f}"), width="stretch")

    st.subheader("Como mudou a preferência")
    base = st.radio("Base do percentual de Lula", ["Votos válidos", "Votos totais (com brancos e nulos)"],
                    horizontal=True, key=f"base_{rotulo}")
    suf = "" if base == "Votos válidos" else "_TOTAL"
    x_col, y_col = f"PCT_LULA{suf}_1t", f"PCT_LULA{suf}_2t"
    g1, g2 = st.columns(2)
    with g1:
        fig = px.scatter(df, x=x_col, y=y_col, color="MUDOU_VENCEDOR", opacity=.6,
                         color_discrete_map={"Sim": COR_LULA, "Não": COR_POP},
                         labels={x_col: "% Lula — 1º turno", y_col: "% Lula — 2º turno"},
                         hover_data=["NR_ZONA", "NR_SECAO"])
        fig.add_trace(go.Scatter(x=[0, 100], y=[0, 100], mode="lines", line=dict(dash="dot", color="gray"),
                                 name="sem mudança", hoverinfo="skip"))
        fig.update_layout(height=400, margin=dict(t=30), title=f"% de Lula por seção: 1º × 2º turno ({base.split(' (')[0].lower()})")
        st.plotly_chart(fig, width="stretch")
    with g2:
        t = pd.crosstab(df.NR_ZONA, df.TRAJETORIA)
        t = t.div(t.sum(axis=1), axis=0).mul(100).reset_index().melt("NR_ZONA", var_name="trajetória", value_name="%")
        fig = px.bar(t, x="NR_ZONA", y="%", color="trajetória", title="Trajetória das seções por zona (%)",
                     labels={"NR_ZONA": "zona eleitoral"},
                     color_discrete_sequence=[COR_FLAVIO, COR_LULA, "#E08E0B", "#2E8B57"])
        fig.update_layout(height=400, margin=dict(t=30))
        st.plotly_chart(fig, width="stretch")


def comparacao(pop, amo):
    st.subheader("Comparação população × amostra")
    st.caption("Diferenças entre a amostra e a população (mesmo filtro de zona aplicado a ambas).")
    cols = list(QUANTI)
    dp, da = descritivas(pop, cols), descritivas(amo, cols)
    comp = pd.DataFrame({
        "média pop.": dp["média"], "média amostra": da["média"], "diferença": da["média"] - dp["média"],
        "mediana pop.": dp["mediana"], "mediana amostra": da["mediana"],
        "dp pop.": dp["desvio-padrão"], "dp amostra": da["desvio-padrão"],
    })
    st.dataframe(comp.style.format("{:.2f}"), width="stretch")

    var = st.selectbox("Sobrepor distribuições da variável", cols, format_func=QUANTI.get, key="cmp_var")
    fig = go.Figure()
    fig.add_histogram(x=pop[var], histnorm="probability density", name="População", marker_color=COR_POP,
                      opacity=.55, nbinsx=30)
    fig.add_histogram(x=amo[var], histnorm="probability density", name="Amostra", marker_color=COR_AMO,
                      opacity=.55, nbinsx=30)
    fig.update_layout(barmode="overlay", height=380, margin=dict(t=20), xaxis_title=QUANTI[var],
                      yaxis_title="densidade")
    st.plotly_chart(fig, width="stretch")

    cat = st.selectbox("Comparar proporções da variável", [c for c in QUALI if c != "NR_ZONA"] + ["NR_ZONA"],
                       format_func=QUALI.get, key="cmp_cat")
    fp, fa = frequencias(pop, cat), frequencias(amo, cat)
    m = fp.merge(fa, on="categoria", how="outer", suffixes=(" pop.", " amostra")).fillna(0)
    m["diferença (p.p.)"] = m["proporção (%) amostra"] - m["proporção (%) pop."]
    g1, g2 = st.columns([3, 2])
    with g1:
        long = m.melt("categoria", ["proporção (%) pop.", "proporção (%) amostra"], var_name="grupo", value_name="%")
        long["grupo"] = long.grupo.str.replace("proporção (%) ", "", regex=False)
        fig = px.bar(long, x="categoria", y="%", color="grupo", barmode="group",
                     color_discrete_map={"pop.": COR_POP, "amostra": COR_AMO})
        fig.update_layout(height=360, margin=dict(t=20))
        st.plotly_chart(fig, width="stretch")
    with g2:
        st.dataframe(m[["categoria", "proporção (%) pop.", "proporção (%) amostra", "diferença (p.p.)"]]
                     .style.format("{:.2f}", subset=["proporção (%) pop.", "proporção (%) amostra", "diferença (p.p.)"]),
                     width="stretch", hide_index=True)


# ---------------------------------------------------------------- app
pop_full, amo_full = carrega("populacao.csv"), carrega("amostra.csv")

st.sidebar.title("🗳️ Eleições 2026")
st.sidebar.caption("Porto Alegre · Presidente · 1º e 2º turnos. Unidade: seção eleitoral. Fonte: TSE (boletins de urna).")
painel = st.sidebar.radio("Painel", ["1 — População", "2 — Amostra"])
zonas = sorted(pop_full.NR_ZONA.unique(), key=int)
sel = st.sidebar.multiselect("Zonas eleitorais", zonas, default=zonas)
if not sel:
    st.warning("Selecione ao menos uma zona.")
    st.stop()
pop, amo = pop_full[pop_full.NR_ZONA.isin(sel)], amo_full[amo_full.NR_ZONA.isin(sel)]
st.sidebar.caption(f"População: {len(pop_full)} seções · Amostra (AAS): {len(amo_full)} seções")

if painel.startswith("1"):
    st.title("Painel 1 — Análise descritiva da população")
    st.caption(f"Todas as {len(pop)} seções eleitorais de Porto Alegre nos filtros selecionados.")
    painel_descritivo(pop, COR_POP, "pop")
else:
    st.title("Painel 2 — Análise descritiva da amostra")
    st.caption(f"Amostra aleatória simples (sem reposição, semente 42): {len(amo)} seções nos filtros selecionados.")
    painel_descritivo(amo, COR_AMO, "amo")
    st.divider()
    comparacao(pop, amo)
