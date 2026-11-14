"""Painéis 1 e 2 — Análise descritiva da população e da amostra (Streamlit).

Eleições 2026, Porto Alegre, Presidente: seções eleitorais, 1º e 2º turnos (fonte: TSE, boletins de urna).
Executar:  streamlit run dashboard/app.py
"""
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

DADOS = Path(__file__).resolve().parent / "dados"
FONTE = "https://dadosabertos.tse.jus.br/dataset/resultados-2026-boletim-de-urna"
COR_LULA, COR_FLAVIO, COR_EMPATE = "#C0392B", "#1F4E9C", "#9AA5B1"
COR_POP, COR_AMO = "#6C7A89", "#E08E0B"

# Cor fixa por categoria: a mesma categoria tem a mesma cor em todos os gráficos, com ou sem filtro.
# A ordem deste dicionário também define a ordem das categorias nos gráficos e nas tabelas.
CORES_CAT = {
    "LULA": COR_LULA, "FLAVIO BOLSONARO": COR_FLAVIO, "EMPATE": COR_EMPATE,
    "LULA → LULA": COR_LULA, "FLAVIO → LULA": "#F1948A", "EMPATE → LULA": "#E6B0AA",
    "FLAVIO → FLAVIO": COR_FLAVIO, "LULA → FLAVIO": "#85A9DC", "EMPATE → FLAVIO": "#AEC6E8",
    "LULA → EMPATE": "#B3B6B7", "FLAVIO → EMPATE": "#7F8C8D",
    "Não": "#AAB7B8", "Sim": "#8E44AD", "Indefinido (empate)": "#D4AC0D",
}

QUANTI = {
    "PCT_LULA_1t": "% Lula — 1º turno (votos válidos)",
    "PCT_LULA_2t": "% Lula — 2º turno (votos válidos)",
    "DELTA_LULA_PP": "Variação do % de Lula (2º − 1º, p.p.) — votos válidos",
    "PCT_FLAVIO_1t": "% Flávio Bolsonaro — 1º turno (votos válidos)",
    "PCT_FLAVIO_2t": "% Flávio Bolsonaro — 2º turno (votos válidos)",
    "PCT_OUTROS_1t": "% dos demais candidatos — 1º turno (votos válidos)",
    "PCT_LULA_TOTAL_1t": "% Lula — 1º turno (votos totais, com brancos e nulos)",
    "PCT_LULA_TOTAL_2t": "% Lula — 2º turno (votos totais, com brancos e nulos)",
    "DELTA_LULA_TOTAL_PP": "Variação do % de Lula (2º − 1º, p.p.) — votos totais",
    "PCT_BRANCO_NULO_1t": "% de brancos e nulos — 1º turno (votos totais)",
    "PCT_BRANCO_NULO_2t": "% de brancos e nulos — 2º turno (votos totais)",
    "PCT_ABSTENCAO_1t": "% de abstenção — 1º turno",
    "PCT_ABSTENCAO_2t": "% de abstenção — 2º turno",
    "DELTA_ABST_PP": "Variação da abstenção (2º − 1º, p.p.)",
    "QT_APTOS_1t": "Eleitores aptos por seção",
}
QUALI = {
    "VENCEDOR_1t": "Vencedor da seção — 1º turno",
    "VENCEDOR_2t": "Vencedor da seção — 2º turno",
    "MUDOU_VENCEDOR": "Mudou de vencedor entre os turnos?",
    "TRAJETORIA": "Trajetória (1º → 2º turno)",
    "NR_ZONA": "Zona eleitoral",
}
# Pares da mesma medida nos dois turnos, para as comparações pareadas (mesma seção).
PARES = {
    "% Lula (votos válidos)": ("PCT_LULA_1t", "PCT_LULA_2t"),
    "% Flávio Bolsonaro (votos válidos)": ("PCT_FLAVIO_1t", "PCT_FLAVIO_2t"),
    "% Lula (votos totais)": ("PCT_LULA_TOTAL_1t", "PCT_LULA_TOTAL_2t"),
    "% de brancos e nulos": ("PCT_BRANCO_NULO_1t", "PCT_BRANCO_NULO_2t"),
    "% de abstenção": ("PCT_ABSTENCAO_1t", "PCT_ABSTENCAO_2t"),
}
# (tipo, como é calculada) — alimenta a seção "Sobre os dados e as variáveis".
DESCRICAO = {
    "PCT_LULA_1t": ("Quantitativa contínua", "Votos de Lula ÷ votos válidos da seção × 100."),
    "PCT_LULA_2t": ("Quantitativa contínua", "Idem, no 2º turno (só Lula e Flávio na disputa)."),
    "DELTA_LULA_PP": ("Quantitativa contínua", "% Lula no 2º turno − % Lula no 1º turno, na mesma seção (medida pareada)."),
    "PCT_FLAVIO_1t": ("Quantitativa contínua", "Votos de Flávio Bolsonaro ÷ votos válidos da seção × 100."),
    "PCT_FLAVIO_2t": ("Quantitativa contínua", "Idem, no 2º turno."),
    "PCT_OUTROS_1t": ("Quantitativa contínua", "100 − % Lula − % Flávio no 1º turno: votos que precisaram mudar de candidato no 2º turno."),
    "PCT_LULA_TOTAL_1t": ("Quantitativa contínua", "Votos de Lula ÷ votos totais (válidos + brancos + nulos) × 100."),
    "PCT_LULA_TOTAL_2t": ("Quantitativa contínua", "Idem, no 2º turno."),
    "DELTA_LULA_TOTAL_PP": ("Quantitativa contínua", "Variação de % Lula sobre votos totais entre os turnos."),
    "PCT_BRANCO_NULO_1t": ("Quantitativa contínua", "(Brancos + nulos) ÷ votos totais × 100."),
    "PCT_BRANCO_NULO_2t": ("Quantitativa contínua", "Idem, no 2º turno."),
    "PCT_ABSTENCAO_1t": ("Quantitativa contínua", "Abstenções ÷ eleitores aptos × 100."),
    "PCT_ABSTENCAO_2t": ("Quantitativa contínua", "Idem, no 2º turno."),
    "DELTA_ABST_PP": ("Quantitativa contínua", "Abstenção no 2º turno − no 1º turno; negativo = mais eleitores votaram no 2º turno."),
    "QT_APTOS_1t": ("Quantitativa discreta", "Eleitores aptos a votar na seção (1º turno). Mede o tamanho da seção."),
    "VENCEDOR_1t": ("Qualitativa nominal", "Candidato com mais votos na seção; EMPATE quando Lula e Flávio têm o mesmo número de votos."),
    "VENCEDOR_2t": ("Qualitativa nominal", "Idem, no 2º turno."),
    "MUDOU_VENCEDOR": ("Qualitativa nominal", "Sim: o vencedor trocou entre Lula e Flávio. Não: mesmo vencedor. Indefinido: empate em algum turno."),
    "TRAJETORIA": ("Qualitativa nominal", "Vencedor no 1º turno → vencedor no 2º turno."),
    "NR_ZONA": ("Qualitativa nominal", "Zona eleitoral (10 zonas). É um código do TSE: categoria, não número."),
}

st.set_page_config(page_title="IA003 — Trabalho Final · Eleições 2026 em Porto Alegre", page_icon="🗳️", layout="wide")


@st.cache_data
def carrega(nome):
    df = pd.read_csv(DADOS / nome)
    df["NR_ZONA"] = df["NR_ZONA"].astype(str)
    return df


def ordem(col, valores):
    """Ordem estável das categorias: zonas pelo número; as demais pela ordem de CORES_CAT."""
    valores = list(dict.fromkeys(valores))
    if col == "NR_ZONA":
        return sorted(valores, key=int)
    pos = list(CORES_CAT)
    return sorted(valores, key=lambda v: pos.index(v) if v in pos else len(pos))


def eixo_categorico(fig, col, valores, titulo):
    # Sem isto o Plotly lê os códigos de zona ("1", "111", "161") como números e cria um eixo de 0 a 160.
    fig.update_xaxes(type="category", categoryorder="array", categoryarray=ordem(col, valores), title=titulo)


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
    f = df[col].value_counts()
    f = f.reindex(ordem(col, f.index))
    return pd.DataFrame({"categoria": f.index, "frequência": f.values, "proporção (%)": f.values / f.sum() * 100})


def milhar(v):
    return f"{v:,}".replace(",", ".")


def pagina_dados():
    """Aba que explica a fonte, o tratamento e as variáveis (sem filtros: vale para os dois painéis)."""
    st.title("📖 Dados")
    st.caption("De onde vêm os dados, como foram tratados e o que significa cada variável dos painéis.")

    st.subheader("Fonte")
    st.markdown(f"""
- **Instituição:** Tribunal Superior Eleitoral (TSE), Portal de Dados Abertos.
- **Conjunto de dados:** [Resultados 2026 — Boletim de Urna]({FONTE}), licença Creative Commons Atribuição.
- **Arquivos usados:** `bweb_1t_RS_051020261403.csv` (1º turno, gerado em 05/10/2026) e
  `bweb_2t_RS_261020260742.csv` (2º turno, gerado em 26/10/2026), ambos do Rio Grande do Sul.
- **O que é um boletim de urna (BU):** o resultado oficial impresso e publicado por cada urna ao fim da votação.
  Registra eleitores aptos, comparecimento, abstenções e os votos de cada candidato, além de brancos e nulos.
- **Leiaute:** CSV em `latin1`, separador `;`, 46 colunas, uma linha por seção × cargo × votável
  (formato longo). Descrição das colunas no arquivo `_leiame-boletimurnaweb.pdf` que acompanha os dados.
- **Tamanho dos arquivos do RS:** 3.649.489 linhas no 1º turno e 106.789 no 2º turno.
""")

    st.subheader("Recorte e tratamento")
    st.markdown(f"""
1. **Filtro:** município de Porto Alegre e cargo de Presidente.
2. **Agregação:** o formato longo foi convertido para **uma linha por seção eleitoral** (chave: zona + seção).
   Sortear linhas do arquivo bruto daria mais chance às seções com mais candidatos votados, violando a AAS.
3. **Junção dos turnos:** cada seção recebe as colunas do 1º turno (sufixo `_1t`) e do 2º turno (sufixo `_2t`).
   Ficam as seções presentes nos dois turnos.
4. **Variáveis derivadas:** percentuais, variações entre turnos, vencedor da seção e trajetória (tabela abaixo).
5. **Conferência:** em 100% das seções, comparecimento + abstenções = aptos e válidos + brancos + nulos = comparecimento.
""")

    st.subheader("População, unidade e amostra")
    c = st.columns(4)
    c[0].metric("Seções (N)", milhar(len(pop_full)))
    c[1].metric("Zonas eleitorais", pop_full.NR_ZONA.nunique())
    c[2].metric("Eleitores aptos (1º turno)", milhar(int(pop_full.QT_APTOS_1t.sum())))
    c[3].metric("Amostra (n)", milhar(len(amo_full)))
    st.markdown(f"""
- **População de interesse:** as {milhar(len(pop_full))} seções eleitorais de Porto Alegre presentes nos dois turnos.
- **Unidade de análise:** a seção eleitoral (um boletim de urna). As conclusões valem para **seções**, não para eleitores individuais.
- **Base tratada (usada nos painéis):** {milhar(len(pop_full))} linhas × {pop_full.shape[1]} colunas, uma linha por seção,
  com as colunas do 1º turno (`_1t`), do 2º turno (`_2t`) e as variáveis derivadas.
  A amostra tem {len(amo_full)} linhas × {amo_full.shape[1]} colunas.
- **Votos válidos** = votos nominais em candidatos. **Votos totais** = válidos + brancos + nulos (igual ao comparecimento).
- Como as mesmas seções aparecem nos dois turnos, as variações entre turnos são **pareadas**.
""")

    st.subheader("Dimensionamento da amostra")
    st.markdown("Ferramenta: **Calculadora de tamanho amostral — USP/Bauru** (sugerida no enunciado), com o mesmo "
                "cálculo reproduzido em Python para conferência. O tamanho foi dimensionado para estimar uma "
                "**proporção**, o caso mais exigente.")
    st.latex(r"n_0=\frac{z^2\,p(1-p)}{e^2}=\frac{1{,}96^2\cdot0{,}25}{0{,}03^2}\approx1067"
             r"\qquad n=\frac{n_0}{1+\frac{n_0-1}{N}}\approx793")
    st.table(pd.DataFrame([
        ("Nível de confiança", "95%",
         "Convenção em pesquisas eleitorais e em inferência (z = 1,96); coerente com α = 5% nos testes. "
         "Equilíbrio entre confiança e custo: com 90% o n seria 605; com 99%, 1.153."),
        ("Margem de erro", "3 p.p.",
         "Mesma ordem das pesquisas eleitorais (2 a 3 p.p.) e menor que os efeitos de interesse "
         "(Lula passou de 68% para 75% das seções; ganho médio de ~7 p.p.). Com 2 p.p. → 1.349; 4 p.p. → 503; 5 p.p. → 342."),
        ("Proporção considerada (p)", "0,5",
         "p(1 − p) é máximo em 0,5, então o n vale para qualquer proporção estudada. "
         "Usar o valor da população seria tirar o parâmetro do próprio resultado."),
        ("Tamanho da população (N)", milhar(len(pop_full)), "Seções eleitorais de Porto Alegre."),
        ("Tamanho da amostra (n)", str(len(amo_full)),
         "n₀ = 1.067 sem correção; com a correção para população finita, 793 (fração amostral de 25,8%). "
         "Como a fração passa de 5%, os ICs e testes também usam o fator √((N − n)/(N − 1)) = 0,862."),
    ], columns=["parâmetro", "valor", "justificativa"]).set_index("parâmetro"))
    st.caption("O mesmo n atende às médias: com desvio-padrão ≈ 2,2 p.p. em DELTA_LULA_PP, "
               "a margem de erro da média fica em ≈ 0,13 p.p.")

    st.subheader("Seleção da amostra aleatória simples (AAS)")
    st.markdown(f"""
1. **Cadastro:** as {milhar(len(pop_full))} seções, uma por linha, com chave zona + seção única. O sorteio é feito
   **depois** da agregação: sortear linhas do arquivo bruto daria mais chance às seções com mais candidatos votados.
2. **Sorteio:** `pop.sample(n={len(amo_full)}, replace=False, random_state=42)` (pandas). Equivale a numerar as seções
   de 1 a N e sortear {len(amo_full)} números sem reposição.
3. **Probabilidade igual:** todo subconjunto de {len(amo_full)} seções tem a mesma chance de ser escolhido, então cada
   seção tem probabilidade de inclusão n/N = {len(amo_full)}/{milhar(len(pop_full))} = **{f"{len(amo_full) / len(pop_full):.1%}".replace(".", ",")}**.
4. **Reprodutibilidade:** mesma semente e mesma ordem de linhas geram exatamente a mesma amostra
   (script `dashboard/preparar_dados.py`).
5. **Semente fixada antes da análise:** a semente 42 não foi trocada depois de ver os resultados, mesmo quando uma
   estimativa saiu atípica. Trocar a semente para "melhorar" a amostra invalidaria a inferência.
6. **Representatividade:** a distribuição das seções por zona na amostra é compatível com a da população
   (qui-quadrado de aderência: χ² = 6,0; valor-p = 0,74).
""")

    st.subheader("Variáveis")
    linhas = [{"variável": {**QUANTI, **QUALI}[c], "coluna": c, "tipo": tipo, "como é calculada": desc}
              for c, (tipo, desc) in DESCRICAO.items()]
    st.table(pd.DataFrame(linhas).set_index("variável"))   # st.table quebra o texto longo em várias linhas

    st.subheader("Limitações da fonte")
    st.markdown("""
- Os dados são agregados por seção: não há informação sobre o voto de cada eleitor (o voto é secreto).
- O recorte é apenas Porto Alegre; os resultados não se estendem ao estado nem ao país.
- O número de aptos pode variar levemente entre os turnos na mesma seção (transferências e ajustes do cadastro).
""")


def kpis(df):
    c = st.columns(3)
    c[0].metric("Seções", f"{len(df):,}".replace(",", "."))
    c[1].metric("Eleitores aptos", f"{int(df.QT_APTOS_1t.sum()):,}".replace(",", "."))
    c[2].metric("Mudaram de vencedor", f"{(df.MUDOU_VENCEDOR == 'Sim').mean():.1%}")
    c = st.columns(3)
    c[0].metric("Seções de Lula — 1º turno", f"{(df.VENCEDOR_1t == 'LULA').mean():.1%}")
    c[1].metric("Seções de Lula — 2º turno", f"{(df.VENCEDOR_2t == 'LULA').mean():.1%}")
    c[2].metric("Abstenção média (1º → 2º)", f"{df.PCT_ABSTENCAO_1t.mean():.1f}% → {df.PCT_ABSTENCAO_2t.mean():.1f}%")


def grafico_qq(x, cor, rotulo):
    """Q-Q normal: compara os quantis observados com os de uma normal de mesma média e desvio-padrão."""
    x = np.sort(x.dropna().to_numpy())
    n = len(x)
    z = np.array([NormalDist().inv_cdf((i - 0.375) / (n + 0.25)) for i in range(1, n + 1)])  # posições de Blom
    m, s = x.mean(), x.std(ddof=1)
    fig = go.Figure()
    fig.add_scatter(x=z, y=x, mode="markers", marker=dict(color=cor, size=4, opacity=.6), name="seções")
    fig.add_scatter(x=[z[0], z[-1]], y=[m + s * z[0], m + s * z[-1]], mode="lines",
                    line=dict(dash="dash", color="gray"), name="normal de referência")
    fig.update_layout(title="Q-Q normal", xaxis_title="quantil teórico da normal padrão", yaxis_title=rotulo,
                      height=380, margin=dict(t=40), showlegend=False)
    return fig


def bloco_quantitativas(df, cor, rotulo, zonas):
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

    g1, g2 = st.columns(2)
    with g1:
        fig = px.box(df, x="NR_ZONA", y=var, color_discrete_sequence=[cor], points=False,
                     labels={var: QUANTI[var]}, hover_data=["NR_SECAO"])
        fig.add_hline(y=df[var].mean(), line_dash="dash", line_color="gray", annotation_text="média geral")
        eixo_categorico(fig, "NR_ZONA", zonas, "zona eleitoral")
        fig.update_layout(height=380, margin=dict(t=40), title="Distribuição por zona eleitoral")
        st.plotly_chart(fig, width="stretch")
    with g2:
        st.plotly_chart(grafico_qq(df[var], cor, QUANTI[var]), width="stretch")
    st.caption("Boxplot por zona: compara mediana e dispersão entre regiões da cidade. "
               "Q-Q normal: pontos sobre a reta indicam distribuição próxima da normal; desvios nas pontas indicam "
               "caudas mais pesadas. Para o teste t com n grande, o TCL torna a média amostral aproximadamente normal "
               "mesmo com desvios moderados.")
    with st.expander("Medidas descritivas de todas as variáveis quantitativas"):
        st.dataframe(descritivas(df, list(QUANTI)).style.format("{:.2f}"), width="stretch")


def bloco_turnos(df, cor, rotulo):
    st.subheader("Comparação entre os turnos (mesma seção)")
    par = st.selectbox("Medida", list(PARES), key=f"par_{rotulo}")
    c1, c2 = PARES[par]
    g1, g2 = st.columns(2)
    with g1:
        longo = (df[[c1, c2]].rename(columns={c1: "1º turno", c2: "2º turno"})
                 .melt(var_name="turno", value_name=par))
        fig = px.violin(longo, x="turno", y=par, box=True, color="turno",
                        color_discrete_sequence=["#AAB7B8", cor])
        fig.update_layout(height=420, showlegend=False, margin=dict(t=40), title="Distribuição em cada turno")
        st.plotly_chart(fig, width="stretch")
    with g2:
        lo, hi = min(df[c1].min(), df[c2].min()), max(df[c1].max(), df[c2].max())
        pad = (hi - lo) * .05
        fig = px.scatter(df, x=c1, y=c2, color="MUDOU_VENCEDOR", opacity=.6, color_discrete_map=CORES_CAT,
                         category_orders={"MUDOU_VENCEDOR": ordem("MUDOU_VENCEDOR", df.MUDOU_VENCEDOR)},
                         labels={c1: f"{par} — 1º turno", c2: f"{par} — 2º turno",
                                 "MUDOU_VENCEDOR": "mudou de vencedor?"},
                         hover_data=["NR_ZONA", "NR_SECAO"])
        fig.add_scatter(x=[lo - pad, hi + pad], y=[lo - pad, hi + pad], mode="lines", name="sem mudança",
                        line=dict(dash="dot", color="gray"), hoverinfo="skip")
        fig.update_layout(height=420, margin=dict(t=40), title="Cada ponto é uma seção: 1º × 2º turno")
        st.plotly_chart(fig, width="stretch")
    dif = df[c2] - df[c1]
    st.caption(f"Acima da diagonal, o valor aumentou no 2º turno. Variação média: {dif.mean():+.2f} p.p. "
               f"(desvio-padrão {dif.std():.2f} p.p.); {(dif > 0).mean():.1%} das seções aumentaram.")


def bloco_qualitativas(df, cor, rotulo, zonas):
    st.subheader("Variáveis qualitativas")
    cat = st.selectbox("Variável", list(QUALI), format_func=QUALI.get, key=f"c_{rotulo}")
    f = frequencias(df, cat)
    g1, g2 = st.columns([3, 2])
    with g1:
        fig = px.bar(f, x="categoria", y="frequência", text=f["proporção (%)"].map("{:.1f}%".format),
                     color="categoria", color_discrete_map=CORES_CAT, color_discrete_sequence=[cor])
        eixo_categorico(fig, cat, f.categoria, QUALI[cat])
        fig.update_layout(height=380, showlegend=False, margin=dict(t=20), yaxis_title="nº de seções")
        st.plotly_chart(fig, width="stretch")
    with g2:
        st.markdown("**Frequências e proporções**")
        st.dataframe(f.style.format({"proporção (%)": "{:.2f}"}), width="stretch", hide_index=True)

    if cat != "NR_ZONA":
        t = (pd.crosstab(df.NR_ZONA, df[cat], normalize="index").mul(100).reset_index()
             .melt("NR_ZONA", var_name="categoria", value_name="%"))
        fig = px.bar(t, x="NR_ZONA", y="%", color="categoria", color_discrete_map=CORES_CAT,
                     category_orders={"categoria": ordem(cat, t.categoria)},
                     title=f"{QUALI[cat]} — composição por zona (%)")
        eixo_categorico(fig, "NR_ZONA", zonas, "zona eleitoral")
        fig.update_layout(height=380, margin=dict(t=40), legend_title=None, yaxis_range=[0, 100])
        st.plotly_chart(fig, width="stretch")
        st.caption("Cada barra soma 100%: mostra se a proporção muda entre as regiões da cidade.")


def bloco_transicao(df, cor):
    st.subheader("Transição do vencedor e origem do ganho de Lula")
    g1, g2 = st.columns(2)
    with g1:
        o1, o2 = ordem("VENCEDOR_1t", df.VENCEDOR_1t), ordem("VENCEDOR_2t", df.VENCEDOR_2t)
        m = pd.crosstab(df.VENCEDOR_1t, df.VENCEDOR_2t).reindex(index=o1, columns=o2, fill_value=0)
        pct = m / m.values.sum() * 100
        texto = m.astype(str) + "<br>(" + pct.round(1).astype(str) + "%)"
        fig = go.Figure(go.Heatmap(z=m.values, x=o2, y=o1, text=texto.values, texttemplate="%{text}",
                                   colorscale=[[0, "#F4F6F7"], [1, "#AAB7B8"]], showscale=False,
                                   hovertemplate="1º turno: %{y}<br>2º turno: %{x}<br>seções: %{z}<extra></extra>"))
        fig.update_xaxes(type="category", title="vencedor no 2º turno")
        fig.update_yaxes(type="category", title="vencedor no 1º turno", autorange="reversed")
        fig.update_layout(height=380, margin=dict(t=40), title="Matriz de transição (nº de seções e % do total)")
        st.plotly_chart(fig, width="stretch")
    with g2:
        x, y = df.PCT_OUTROS_1t, df.DELTA_LULA_PP
        fig = px.scatter(df, x="PCT_OUTROS_1t", y="DELTA_LULA_PP", opacity=.5, color_discrete_sequence=[cor],
                         labels={"PCT_OUTROS_1t": QUANTI["PCT_OUTROS_1t"], "DELTA_LULA_PP": "Variação do % de Lula (p.p.)"},
                         hover_data=["NR_ZONA", "NR_SECAO"])
        xs = np.array([x.min(), x.max()])
        fig.add_scatter(x=xs, y=xs / 2, mode="lines", name="Lula herda metade dos demais",
                        line=dict(dash="dot", color="gray"))
        titulo = "Ganho de Lula × votos dos demais candidatos no 1º turno"
        if len(df) > 2:
            a, b = np.polyfit(x, y, 1)   # reta de mínimos quadrados, só para mostrar a tendência
            fig.add_scatter(x=xs, y=a * xs + b, mode="lines", name="tendência (MQO)", line=dict(color="black"))
            titulo += f" (r = {x.corr(y):.2f})"
        fig.update_layout(height=380, margin=dict(t=40), title=titulo,
                          legend=dict(orientation="h", yanchor="bottom", y=-0.35))
        st.plotly_chart(fig, width="stretch")
    st.caption("Matriz: a diagonal são as seções que mantiveram o vencedor. Dispersão: a linha pontilhada é o ganho "
               "aproximado se Lula herdasse metade dos votos dos demais candidatos; pontos acima dela indicam que herdou "
               "mais que a metade. Cuidado: é uma relação entre seções (dado agregado) e não prova o comportamento de "
               "cada eleitor (falácia ecológica).")


def bloco_composicao(df):
    st.subheader("Composição dos votos (média das seções)")
    st.caption("Votos totais = válidos + brancos + nulos (igual ao comparecimento). No 2º turno só há dois candidatos.")
    comp = []
    for t, nome in (("1t", "1º turno"), ("2t", "2º turno")):
        lula, flavio, bn = (df[f"PCT_LULA_TOTAL_{t}"].mean(), df[f"PCT_FLAVIO_TOTAL_{t}"].mean(),
                            df[f"PCT_BRANCO_NULO_{t}"].mean())
        comp += [(nome, "Lula", lula), (nome, "Flávio Bolsonaro", flavio),
                 (nome, "Outros candidatos", max(0.0, 100 - lula - flavio - bn)), (nome, "Brancos e nulos", bn)]
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


def painel_descritivo(df, cor, rotulo):
    zonas = ordem("NR_ZONA", df.NR_ZONA)
    kpis(df)
    st.divider()
    bloco_quantitativas(df, cor, rotulo, zonas)
    st.divider()
    bloco_turnos(df, cor, rotulo)
    st.divider()
    bloco_qualitativas(df, cor, rotulo, zonas)
    st.divider()
    bloco_transicao(df, cor)
    st.divider()
    bloco_composicao(df)


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

    cat = st.selectbox("Comparar proporções da variável", list(QUALI), format_func=QUALI.get, key="cmp_cat")
    fp, fa = frequencias(pop, cat), frequencias(amo, cat)
    m = fp.merge(fa, on="categoria", how="outer", suffixes=(" pop.", " amostra")).fillna(0)
    m["_ordem"] = m.categoria.map({v: i for i, v in enumerate(ordem(cat, m.categoria))})
    m = m.sort_values("_ordem").drop(columns="_ordem")
    m["diferença (p.p.)"] = m["proporção (%) amostra"] - m["proporção (%) pop."]
    g1, g2 = st.columns([3, 2])
    with g1:
        longo = m.melt("categoria", ["proporção (%) pop.", "proporção (%) amostra"], var_name="grupo", value_name="%")
        longo["grupo"] = longo.grupo.str.replace("proporção (%) ", "", regex=False)
        fig = px.bar(longo, x="categoria", y="%", color="grupo", barmode="group",
                     color_discrete_map={"pop.": COR_POP, "amostra": COR_AMO})
        eixo_categorico(fig, cat, m.categoria, QUALI[cat])
        fig.update_layout(height=360, margin=dict(t=20))
        st.plotly_chart(fig, width="stretch")
    with g2:
        st.dataframe(m[["categoria", "proporção (%) pop.", "proporção (%) amostra", "diferença (p.p.)"]]
                     .style.format("{:.2f}", subset=["proporção (%) pop.", "proporção (%) amostra", "diferença (p.p.)"]),
                     width="stretch", hide_index=True)


# ---------------------------------------------------------------- app
pop_full, amo_full = carrega("populacao.csv"), carrega("amostra.csv")

def filtro_zonas():
    """Filtro de zona na barra lateral, só nos painéis. A seleção é guardada na sessão para
    sobreviver à troca de aba (widgets que não são desenhados perdem o estado no Streamlit)."""
    st.sidebar.title("🗳️ Eleições 2026")
    st.sidebar.caption("Porto Alegre · Presidente · 1º e 2º turnos. Unidade: seção eleitoral. Fonte: TSE (boletins de urna).")
    zonas = ordem("NR_ZONA", pop_full.NR_ZONA)
    sel = st.sidebar.multiselect("Zonas eleitorais", zonas, default=st.session_state.get("zonas_sel", zonas))
    st.session_state["zonas_sel"] = sel
    st.sidebar.caption(f"População: {len(pop_full)} seções · Amostra (AAS): {len(amo_full)} seções")
    if not sel:
        st.warning("Selecione ao menos uma zona na barra lateral.")
        st.stop()
    return pop_full[pop_full.NR_ZONA.isin(sel)], amo_full[amo_full.NR_ZONA.isin(sel)]


def pagina_populacao():
    st.title("🏙️ Painel 1 — Análise descritiva da população")
    pop, _ = filtro_zonas()
    st.caption(f"Todas as {len(pop)} seções eleitorais de Porto Alegre nas zonas selecionadas. "
               "Definições das variáveis na aba 📖 Dados.")
    painel_descritivo(pop, COR_POP, "pop")


def pagina_amostra():
    st.title("🎲 Painel 2 — Análise descritiva da amostra")
    pop, amo = filtro_zonas()
    st.caption(f"Amostra aleatória simples (sem reposição, semente 42): {len(amo)} seções nas zonas selecionadas. "
               "Definições das variáveis na aba 📖 Dados.")
    painel_descritivo(amo, COR_AMO, "amo")
    st.divider()
    comparacao(pop, amo)


# ---------------------------------------------------------------- Painel 3: inferência
COR_REAL = "#2E8B57"   # parâmetro populacional (valor verdadeiro)

# As 4 hipóteses. O valor de referência (H0) vem sempre de fora do parâmetro testado:
# do 1º turno, de uma regra neutra ou de uma convenção — nunca do resultado do 2º turno.
HIPOTESES = [
    dict(id="P1", tipo="proporção", col="VENCEDOR_2t", evento="LULA", alt="maior",
         ref=lambda p: (p.VENCEDOR_1t == "LULA").mean(),
         titulo="P1 — Lula ampliou a proporção de seções vencidas em relação ao 1º turno?",
         parametro="p = proporção de seções em que Lula foi o mais votado no 2º turno.",
         variavel="`VENCEDOR_2t` (qualitativa); evento de interesse: `VENCEDOR_2t = LULA`.",
         justificativa="O valor de referência é o resultado oficial do 1º turno (proporção de seções vencidas por Lula), "
                       "conhecido antes do 2º turno. Teste unilateral porque a pergunta tem direção: Lula ganhou território?",
         sim="Lula venceu em uma proporção de seções maior que no 1º turno.",
         nao="a proporção de seções vencidas por Lula no 2º turno é compatível com a do 1º turno."),
    dict(id="P2", tipo="proporção", col="MUDOU_VENCEDOR", evento="Sim", alt="maior", ref=0.05,
         titulo="P2 — A virada de vencedor foi mais do que um fenômeno raro?",
         parametro="p = proporção de seções em que o vencedor trocou entre Lula e Flávio.",
         variavel="`MUDOU_VENCEDOR` (qualitativa); evento de interesse: `MUDOU_VENCEDOR = Sim`. "
                  "Seções com empate em algum turno contam como \"não virou\".",
         justificativa="Convenção: 5% (1 em cada 20 seções) como limite para um fenômeno \"raro\". É a referência mais "
                       "arbitrária das quatro, e por isso deve ser lida como um limiar de relevância, não como um valor teórico.",
         sim="a virada não foi rara: atingiu mais de 5% das seções.",
         nao="não há evidência de que a virada tenha passado de 5% das seções."),
    dict(id="M1", tipo="média", col="DELTA_LULA_PP", alt="maior",
         ref=lambda p: round(p.PCT_OUTROS_1t.mean() / 2, 2),
         titulo="M1 — Lula herdou mais da metade dos votos dos demais candidatos?",
         parametro="μ = média, entre as seções, da variação do % de Lula (votos válidos) do 1º para o 2º turno, em p.p.",
         variavel="`DELTA_LULA_PP` (quantitativa contínua, pareada: mesma seção nos dois turnos).",
         justificativa="No 1º turno, os demais candidatos tiveram em média 9,47% dos votos válidos por seção. Se esses votos "
                       "se dividissem igualmente entre Lula e Flávio, Lula ganharia cerca de metade disso (4,74 p.p.). "
                       "Testar contra 0 seria trivial: só 2 das 3.077 seções têm variação ≤ 0.",
         sim="o ganho médio de Lula por seção foi maior que o de uma divisão igual: ele herdou mais da metade dos votos "
             "dos demais candidatos (abstenção e brancos/nulos também influem).",
         nao="o ganho médio de Lula é compatível com uma divisão igual dos votos dos demais candidatos."),
    dict(id="M2", tipo="média", col="DELTA_ABST_PP", alt="diferente", ref=0.0,
         titulo="M2 — A abstenção por seção mudou entre os turnos?",
         parametro="μ = média, entre as seções, da variação da abstenção (2º − 1º turno), em p.p.",
         variavel="`DELTA_ABST_PP` (quantitativa contínua, pareada).",
         justificativa="μ = 0 representa nenhuma mudança. Teste bilateral porque a abstenção poderia subir (desinteresse) "
                       "ou cair (mobilização). Complementa M1: parte do ganho de Lula pode vir de quem não votou no 1º turno.",
         sim="a abstenção média por seção mudou entre os turnos.",
         nao="não há evidência de mudança na abstenção média por seção."),
]
OPERADOR = {"maior": ">", "menor": "<", "diferente": "≠"}


def br(v, d=2):
    """Número no formato brasileiro (vírgula decimal, ponto de milhar)."""
    return f"{v:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_valor(h, v):
    return f"{br(v * 100)}%" if h["tipo"] == "proporção" else f"{br(v)} p.p."


def fmt_p(p):
    return "< 0,001" if p < 0.001 else br(p, 3)


def valor_ref(h):
    return h["ref"](pop_full) if callable(h["ref"]) else h["ref"]


def calcula(h, alpha, usar_fpc):
    """IC (1 − α) e teste de hipótese usando SÓ a amostra; o parâmetro real vem da população, só para comparação."""
    N, n = len(pop_full), len(amo_full)
    fpc = np.sqrt((N - n) / (N - 1))            # correção para população finita
    f = fpc if usar_fpc else 1.0
    ref = valor_ref(h)
    if h["tipo"] == "proporção":
        x = amo_full[h["col"]].eq(h["evento"])
        est, real = x.mean(), pop_full[h["col"]].eq(h["evento"]).mean()
        se_ic = np.sqrt(est * (1 - est) / n) * f   # EP do IC: usa p̂
        se_h0 = np.sqrt(ref * (1 - ref) / n) * f   # EP do teste: usa p0 (variância sob H0)
        dist, nome = stats.norm(), "z"
        ep_exato = np.sqrt(real * (1 - real) / n) * fpc
        condicoes = [(f"n·p₀ = {br(n * ref, 0)} ≥ 10", n * ref >= 10),
                     (f"n·(1 − p₀) = {br(n * (1 - ref), 0)} ≥ 10", n * (1 - ref) >= 10)]
    else:
        x = amo_full[h["col"]]
        est, real = x.mean(), pop_full[h["col"]].mean()
        se_ic = se_h0 = x.std(ddof=1) / np.sqrt(n) * f   # σ desconhecido: usa s (teste t)
        dist, nome = stats.t(n - 1), "t"
        ep_exato = pop_full[h["col"]].std(ddof=1) / np.sqrt(n) * fpc
        g = x.skew()
        condicoes = [(f"n = {n} ≥ 30: pelo TCL, a média amostral é aproximadamente normal", n >= 30),
                     (f"distribuição quase simétrica (assimetria = {br(g)})", abs(g) < 1)]
    condicoes += [("amostra aleatória simples, sem reposição", True),
                  (f"fração amostral n/N = {br(n / N * 100, 1)}% > 5%: " +
                   ("correção para população finita aplicada" if usar_fpc else "SEM correção: IC e teste conservadores"),
                   usar_fpc)]
    stat = (est - ref) / se_h0
    pval = {"maior": dist.sf(stat), "menor": dist.cdf(stat), "diferente": 2 * dist.sf(abs(stat))}[h["alt"]]
    crit = dist.ppf(1 - alpha / 2)
    lo, hi = est - crit * se_ic, est + crit * se_ic
    # Com a população conhecida, sabemos se H1 é de fato verdadeira e, portanto, se o teste acertou.
    h1_real = {"maior": real > ref, "menor": real < ref, "diferente": not np.isclose(real, ref)}[h["alt"]]
    return dict(n=n, ref=ref, est=est, real=real, lo=lo, hi=hi, se=se_ic, stat=stat, nome=nome, pval=pval,
                rejeita=pval < alpha, cobre=lo <= real <= hi, erro=est - real, z_erro=(est - real) / ep_exato,
                h1_real=h1_real, acertou=(pval < alpha) == h1_real, condicoes=condicoes)


def grafico_ic(h, r, conf):
    k = 100 if h["tipo"] == "proporção" else 1
    fig = go.Figure()
    fig.add_scatter(x=[r["est"] * k], y=["amostra"], mode="markers", marker=dict(size=13, color=COR_AMO),
                    error_x=dict(type="data", symmetric=False, array=[(r["hi"] - r["est"]) * k],
                                 arrayminus=[(r["est"] - r["lo"]) * k], thickness=3, width=12, color=COR_AMO),
                    hovertemplate=f"estimativa: %{{x:.2f}}<br>IC {conf}: {r['lo'] * k:.2f} a {r['hi'] * k:.2f}<extra></extra>")
    fig.add_vline(x=r["real"] * k, line_color=COR_REAL, line_width=3,
                  annotation_text="população (real)", annotation_position="top")
    fig.add_vline(x=r["ref"] * k, line_dash="dash", line_color="black",
                  annotation_text="H₀", annotation_position="bottom")
    fig.update_layout(height=200, showlegend=False, margin=dict(t=40, b=40, l=10, r=10),
                      xaxis_title="%" if k == 100 else "p.p.", yaxis_visible=False)
    return fig


def bloco_hipotese(h, r, alpha, conf):
    st.subheader(h["titulo"])
    simb = "p" if h["tipo"] == "proporção" else "μ"
    ref_txt = fmt_valor(h, r["ref"])
    g1, g2 = st.columns([3, 2])
    with g1:
        st.markdown(f"""
- **Parâmetro:** {h['parametro']}
- **Variável:** {h['variavel']}
- **Hipóteses:** H₀: {simb} = {ref_txt} · H₁: {simb} {OPERADOR[h['alt']]} {ref_txt}
  ({'unilateral' if h['alt'] != 'diferente' else 'bilateral'}; α = {br(alpha * 100, 0)}%)
- **Por que este valor de referência:** {h['justificativa']}
""")
        st.markdown("**Condições de aplicação**  \n" + "  \n".join(
            f"{'✅' if ok else '⚠️'} {txt}" for txt, ok in r["condicoes"]))
    with g2:
        st.plotly_chart(grafico_ic(h, r, conf), width="stretch")
        st.caption(f"Ponto e barra: estimativa e IC {conf} da amostra. Linha verde: parâmetro real (população). "
                   "Linha tracejada: valor de H₀.")

    c = st.columns([1, 1.4, 1, 1, 1.1])
    k, unid = (100, "%") if h["tipo"] == "proporção" else (1, "p.p.")
    c[0].metric("Estimativa (amostra)", fmt_valor(h, r["est"]))
    c[1].metric(f"IC {conf} ({unid})", f"{br(r['lo'] * k)} a {br(r['hi'] * k)}")
    c[2].metric(f"Estatística {r['nome']}", br(r["stat"]))
    c[3].metric("Valor-p", fmt_p(r["pval"]))
    c[4].metric("Decisão", "Rejeita H₀" if r["rejeita"] else "Não rejeita H₀")

    if h["id"] == "M2" and r["rejeita"]:
        sentido = "caiu" if r["est"] < 0 else "subiu"
        conclusao = f"{h['sim']} Ela {sentido}, em média, {fmt_valor(h, abs(r['est']))} por seção."
    else:
        conclusao = h["sim"] if r["rejeita"] else h["nao"]
    p_txt = "valor-p < 0,001" if r["pval"] < 0.001 else f"valor-p = {fmt_p(r['pval'])}"
    texto = (f"**Conclusão:** {p_txt} {'<' if r['rejeita'] else '≥'} α = {br(alpha, 2)}, "
             f"{'rejeita-se' if r['rejeita'] else 'não se rejeita'} H₀ — {conclusao}")
    (st.success if r["rejeita"] else st.info)(texto)

    distancia = abs(r["z_erro"])
    leitura = ("dentro do esperado para uma AAS" if distancia < 2 else
               "uma diferença incomum: só uma pequena fração das amostras possíveis erra tanto")
    st.markdown(
        f"**Comparação com a população:** o parâmetro real é **{fmt_valor(h, r['real'])}**. "
        f"A estimativa errou por {fmt_valor(h, r['erro'])}, o equivalente a {br(distancia)} erros-padrão — {leitura}. "
        f"O IC {conf} **{'contém' if r['cobre'] else 'NÃO contém'}** o valor real"
        + ("." if r["cobre"] else
           f": é o risco previsto pela confiança de {conf} — numa fração das amostras, o IC não captura o parâmetro.")
        + (f" Na população, H₁ é {'verdadeira' if r['h1_real'] else 'falsa'}, então a decisão do teste "
           f"{'acertou' if r['acertou'] else 'errou (' + ('erro tipo I' if r['rejeita'] else 'erro tipo II') + ')'}."))


@st.cache_data(show_spinner="Sorteando 1.000 amostras…")
def simulacao(alpha, usar_fpc, B=1000, semente=2026):
    """Repete a AAS B vezes para medir a cobertura real dos ICs e a taxa de rejeição de H0 de cada hipótese."""
    N, n = len(pop_full), len(amo_full)
    f = np.sqrt((N - n) / (N - 1)) if usar_fpc else 1.0
    rng = np.random.default_rng(semente)
    idx = np.stack([rng.choice(N, n, replace=False) for _ in range(B)])   # B amostras × n seções
    out = {}
    for h in HIPOTESES:
        ref = valor_ref(h)
        if h["tipo"] == "proporção":
            v = pop_full[h["col"]].eq(h["evento"]).to_numpy(float)
            real, amostras = v.mean(), v[idx]
            est = amostras.mean(axis=1)
            se_ic, se_h0 = np.sqrt(est * (1 - est) / n) * f, np.sqrt(ref * (1 - ref) / n) * f
            dist = stats.norm()
        else:
            v = pop_full[h["col"]].to_numpy(float)
            real, amostras = v.mean(), v[idx]
            est = amostras.mean(axis=1)
            se_ic = se_h0 = amostras.std(axis=1, ddof=1) / np.sqrt(n) * f
            dist = stats.t(n - 1)
        crit = dist.ppf(1 - alpha / 2)
        stat = (est - ref) / se_h0
        pval = {"maior": dist.sf(stat), "menor": dist.cdf(stat), "diferente": 2 * dist.sf(np.abs(stat))}[h["alt"]]
        lo, hi = est - crit * se_ic, est + crit * se_ic
        out[h["id"]] = dict(est=est, lo=lo, hi=hi, real=real,
                            cobertura=((lo <= real) & (real <= hi)).mean(), rejeicao=(pval < alpha).mean())
    return out


def bloco_variabilidade(alpha, usar_fpc, conf, resultados):
    st.subheader("Variabilidade amostral: e se outra amostra tivesse sido sorteada?")
    st.markdown("Como a população inteira é conhecida, dá para repetir o sorteio **1.000 vezes** (mesmo n = 793) e ver "
                "com que frequência o IC captura o parâmetro real e o teste rejeita H₀.")
    sim = simulacao(alpha, usar_fpc)
    st.dataframe(pd.DataFrame([{
        "hipótese": h["id"],
        f"cobertura do IC {conf}": f"{br(sim[h['id']]['cobertura'] * 100, 1)}%",
        "taxa de rejeição de H₀": f"{br(sim[h['id']]['rejeicao'] * 100, 1)}%",
        "nossa amostra: IC contém o real?": "sim" if resultados[h["id"]]["cobre"] else "não",
    } for h in HIPOTESES]), width="stretch", hide_index=True)
    st.caption(f"Com a correção para população finita, a cobertura fica perto de {conf}, como prometido. Sem ela, os ICs "
               "ficam mais largos que o necessário e a cobertura passa do nominal (use o controle no topo para comparar).")

    hid = st.selectbox("Ver os 100 primeiros ICs simulados da hipótese", [h["id"] for h in HIPOTESES], index=2,
                       format_func=lambda i: next(h["titulo"] for h in HIPOTESES if h["id"] == i))
    h = next(h for h in HIPOTESES if h["id"] == hid)
    s, k = sim[hid], (100 if h["tipo"] == "proporção" else 1)
    est, lo, hi = s["est"][:100] * k, s["lo"][:100] * k, s["hi"][:100] * k
    cobre = (lo <= s["real"] * k) & (s["real"] * k <= hi)
    fig = go.Figure()
    for mask, cor, nome in ((cobre, COR_POP, "contém o real"), (~cobre, COR_LULA, "não contém")):
        ys = np.arange(1, 101)[mask]
        fig.add_scatter(x=est[mask], y=ys, mode="markers", marker=dict(color=cor, size=5), name=nome,
                        error_x=dict(type="data", symmetric=False, array=(hi - est)[mask],
                                     arrayminus=(est - lo)[mask], color=cor, thickness=1.5, width=0))
    fig.add_vline(x=s["real"] * k, line_color=COR_REAL, line_width=2, annotation_text="valor real")
    fig.update_layout(height=480, margin=dict(t=30), xaxis_title="%" if k == 100 else "p.p.",
                      yaxis_title="amostra simulada", legend=dict(orientation="h", y=-0.15))
    st.plotly_chart(fig, width="stretch")
    st.caption(f"Cada linha é o IC {conf} de uma amostra diferente. Os ICs em vermelho não capturam o parâmetro real: "
               "isso não é erro de cálculo, é o risco assumido pelo nível de confiança.")


def bloco_cidade(alpha, usar_fpc, conf):
    st.subheader("Da seção para a cidade")
    N, n = len(pop_full), len(amo_full)
    f = np.sqrt((N - n) / (N - 1)) if usar_fpc else 1.0
    a, p = amo_full, pop_full
    # Estimador de razão: a unidade sorteada continua sendo a seção (conglomerado de eleitores), por isso o EP
    # usa os resíduos por seção — tratar os ~200 mil votos da amostra como independentes subestimaria o erro.
    R = a.LULA_2t.sum() / a.VOTOS_VALIDOS_2t.sum()
    resid = a.LULA_2t - R * a.VOTOS_VALIDOS_2t
    se = np.sqrt(resid.var(ddof=1) / n) / a.VOTOS_VALIDOS_2t.mean() * f
    crit = stats.norm.ppf(1 - alpha / 2)
    real = p.LULA_2t.sum() / p.VOTOS_VALIDOS_2t.sum()
    st.markdown(
        f"O resultado oficial da cidade é um único número, não uma variável, por isso não é testado diretamente. "
        f"Mas a amostra de seções permite estimá-lo pelo **estimador de razão** (votos de Lula na amostra ÷ votos "
        f"válidos na amostra): **{br(R * 100)}%**, com IC {conf} de **{br((R - crit * se) * 100)}% a "
        f"{br((R + crit * se) * 100)}%**. O resultado oficial de Porto Alegre foi **{br(real * 100)}%** — "
        f"{'dentro' if R - crit * se <= real <= R + crit * se else 'fora'} do intervalo. "
        "Em outras palavras: com 793 urnas sorteadas, o resultado da capital seria estimado com margem de cerca de "
        f"{br(crit * se * 100, 1)} p.p. (esse estimador vai além do conteúdo da disciplina e entra só como complemento).")
    st.dataframe(pd.DataFrame([
        ("% de Lula na cidade (total de votos válidos)", R * 100, real * 100),
        ("Média do % de Lula por seção", a.PCT_LULA_2t.mean(), p.PCT_LULA_2t.mean()),
        ("% de seções vencidas por Lula", a.VENCEDOR_2t.eq("LULA").mean() * 100, p.VENCEDOR_2t.eq("LULA").mean() * 100),
    ], columns=["parâmetro (2º turno)", "amostra", "população"]).style.format("{:.2f}", subset=["amostra", "população"]),
        width="stretch", hide_index=True)
    st.caption("São três parâmetros diferentes. O total e a média por seção ficam próximos porque as seções têm tamanho "
               "parecido; a proporção de seções vencidas é bem maior porque Lula venceu muitas seções por pouco.")


def pagina_inferencia():
    st.title("📐 Painel 3 — Inferência estatística e comparação dos resultados")
    st.caption("Os procedimentos de inferência usam **apenas a amostra** (793 seções). Os parâmetros populacionais são "
               "calculados diretamente das 3.077 seções e servem só para conferir se a inferência acertou. "
               "Sem filtro de zona: a inferência vale para a AAS inteira.")
    c1, c2 = st.columns(2)
    alpha = c1.radio("Nível de significância (α)", [0.01, 0.05, 0.10], index=1, horizontal=True,
                     format_func=lambda a: f"{a:.0%}")
    usar_fpc = c2.toggle("Aplicar correção para população finita", value=True,
                         help="A amostra é 25,8% da população; acima de 5%, as fórmulas usuais superestimam o erro-padrão.")
    conf = f"{1 - alpha:.0%}"
    resultados = {h["id"]: calcula(h, alpha, usar_fpc) for h in HIPOTESES}

    st.subheader("Resumo")
    st.dataframe(pd.DataFrame([{
        "hipótese": h["id"],
        "H₀": f"{'p' if h['tipo'] == 'proporção' else 'μ'} = {fmt_valor(h, r['ref'])}",
        "H₁": f"{'p' if h['tipo'] == 'proporção' else 'μ'} {OPERADOR[h['alt']]} {fmt_valor(h, r['ref'])}",
        "estimativa (amostra)": fmt_valor(h, r["est"]),
        f"IC {conf}": f"{fmt_valor(h, r['lo'])} a {fmt_valor(h, r['hi'])}",
        "estatística": f"{r['nome']} = {br(r['stat'])}",
        "valor-p": fmt_p(r["pval"]),
        "decisão": "rejeita H₀" if r["rejeita"] else "não rejeita H₀",
        "parâmetro real (população)": fmt_valor(h, r["real"]),
        "IC contém o real?": "✅ sim" if r["cobre"] else "❌ não",
    } for h in HIPOTESES for r in [resultados[h["id"]]]]), width="stretch", hide_index=True)
    st.caption(f"IC bilateral de {conf} (= 1 − α). Proporções: teste z com o erro-padrão sob H₀. "
               "Médias: teste t para uma amostra; como DELTA_* é a diferença na mesma seção, equivale ao t pareado.")

    for h in HIPOTESES:
        st.divider()
        bloco_hipotese(h, resultados[h["id"]], alpha, conf)

    st.divider()
    st.subheader("Comparação e interpretação")
    cobrem = sum(r["cobre"] for r in resultados.values())
    rejeitam = sum(r["rejeita"] for r in resultados.values())
    fora = [h["id"] for h in HIPOTESES if not resultados[h["id"]]["cobre"]]
    st.markdown(f"""
- **Parâmetros × estimativas:** as estimativas ficaram próximas dos valores reais, com erros entre
  {br(min(abs(r['z_erro']) for r in resultados.values()))} e {br(max(abs(r['z_erro']) for r in resultados.values()))}
  erros-padrão. Isso é a variabilidade amostral: cada amostra dá uma estimativa um pouco diferente.
- **Estimativa pontual × IC:** {cobrem} dos 4 ICs contêm o parâmetro real{f" ({', '.join(fora)} não contém)" if fora else ""}.
  O IC é uma faixa de valores plausíveis; a estimativa pontual sozinha quase nunca acerta o valor exato.
- **Testes:** {rejeitam} de 4 rejeitam H₀. Com n = 793 e efeitos grandes, os testes rejeitam com folga — por isso a
  interpretação se apoia no **tamanho do efeito** (a distância entre o IC e H₀), não só no valor-p.
- **Os testes acertaram?** Como a população é conhecida, dá para conferir: a decisão foi correta em
  {sum(r['acertou'] for r in resultados.values())} de 4 hipóteses.
""")

    st.divider()
    bloco_variabilidade(alpha, usar_fpc, conf, resultados)
    st.divider()
    bloco_cidade(alpha, usar_fpc, conf)

    st.divider()
    st.subheader("Limitações")
    multipla = 1 - (1 - alpha) ** 4
    st.markdown(f"""
- **Variabilidade amostral:** uma única amostra pode ser atípica. Aqui, {', '.join(fora) or 'nenhuma hipótese'}
  {'teve' if len(fora) == 1 else 'tiveram'} o IC sem o valor real, e a semente **não** foi trocada para "corrigir" isso.
- **Significância × relevância:** com n grande, diferenças pequenas já dão valor-p minúsculo. O valor-p mede evidência
  contra H₀, não a importância do efeito.
- **Valores de referência:** P1 e M1 vêm do 1º turno, M2 da ausência de mudança; P2 usa uma convenção (5%) e é a mais arbitrária.
  P1 trata o resultado do 1º turno como constante; uma comparação pareada de proporções (teste de McNemar) seria a alternativa.
- **Vários testes:** com 4 testes a α = {br(alpha * 100, 0)}%, a chance de pelo menos um falso positivo (se todas as H₀
  fossem verdadeiras) é de {br(multipla * 100, 1)}%. Os valores-p obtidos são tão pequenos que uma correção (Bonferroni) não muda nenhuma decisão.
- **Unidade de análise:** as conclusões valem para **seções**, não para eleitores (falácia ecológica). Média por seção,
  total da cidade e proporção de seções vencidas são parâmetros diferentes.
- **Fração amostral alta (25,8%):** exige a correção para população finita; sem ela, os ICs ficam cerca de 16% mais largos.
- **Recorte:** apenas Porto Alegre e o cargo de Presidente; os resultados não se estendem ao estado ou ao país.
""")


# Navegação horizontal no topo: uma aba por página, cada uma com URL própria (/dados, /populacao, /amostra, /inferencia).
navegacao = st.navigation([
    st.Page(pagina_dados, title="Dados", icon="📖", url_path="dados", default=True),
    st.Page(pagina_populacao, title="Painel 1 — População", icon="🏙️", url_path="populacao"),
    st.Page(pagina_amostra, title="Painel 2 — Amostra", icon="🎲", url_path="amostra"),
    st.Page(pagina_inferencia, title="Painel 3 — Inferência", icon="📐", url_path="inferencia"),
], position="top")

# Cabeçalho comum a todas as abas: identifica o trabalho antes do conteúdo de cada página.
st.caption("UFRGS · Especialização em Inteligência Artificial Avançada · IA003 — Probabilidade e Estatística para IA")
st.markdown("### 🗳️ Trabalho Final — Eleições 2026 em Porto Alegre: "
            "como mudou a preferência para Presidente entre o 1º e o 2º turno")
st.divider()
navegacao.run()
