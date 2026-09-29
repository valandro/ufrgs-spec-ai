"""Pergunta 2 — Como muda a distribuição de faixas de renda conforme a escolaridade?"""

import streamlit as st

import analise as an
import comum
import graficos_interativos as gi
from analise import ESCOLARIDADE

ctx = comum.contexto()
m = ctx.modelos
selecao = ctx.selecao
sel = ctx.mun[selecao & ctx.com_dado]

comum.cabecalho(2, "Como muda a distribuição de faixas de renda conforme o nível de "
                   "escolaridade do município?")
comum.parar_se_vazio(ctx, sel)

base = sel[["pct_sem_rendimento_2010", "pct_ate_1sm_2010"]].sum(axis=1)
comum.cartoes(ctx, sel, [
    ("Escolaridade mediana", an.formatar(sel[ESCOLARIDADE].median(), 1, sufixo="%"),
     "% com ensino médio"),
    ("Sem rendimento ou até 1 SM", an.formatar(base.mean(), 1, sufixo="%"), "média municipal"),
    ("Mais de 5 SM", an.formatar(sel["pct_mais_5sm_2010"].mean(), 1, sufixo="%"),
     "média municipal"),
])

# Controle próprio desta página: vale para o gráfico de faixas e para o mapa, logo abaixo.
st.write("")
agrupamento = st.segmented_control(
    "Agrupar os municípios pela escolaridade em", list(an.AGRUPAMENTOS),
    default=an.AGRUPAMENTO_PADRAO, key="agrupamento",
    help="Os cortes são calculados sobre os 496 municípios do RS. Compare as três opções: "
         "se o padrão aparece em todas, ele não depende de quantos grupos foram usados.")
agrupamento = agrupamento or an.AGRUPAMENTO_PADRAO   # clicar de novo na opção marcada a desmarca
ag = an.AGRUPAMENTOS[agrupamento]                   # n, coluna, rótulos e nome no singular
cores_p2 = an.CORES_P2[agrupamento]
lim = m.p2_limites[agrupamento]

filtrado = len(sel) < m.n
nome_grupo = ag["singular"].lower()   # "tercil", "quartil", "quintil"
comum.secao(
    f"Faixas de renda por {nome_grupo} de escolaridade",
    "Atividade 02" + " · versão interativa", "blue",
    f"Os municípios são ordenados pelo % de ocupados com ensino médio completo e divididos em "
    f"{ag['n']} grupos com o mesmo número de municípios ({agrupamento.lower()}, cerca de "
    f"{m.n // ag['n']} em cada). Cada barra mostra como os ocupados de um grupo se distribuem pelas "
    f"seis faixas de rendimento, da base (sem rendimento) ao topo (mais de 5 salários mínimos): é "
    f"a média das distribuições dos municípios do grupo. Os limites dos grupos são os do estado; "
    f"com filtro, as barras mostram só os municípios da seleção.")


def pct(v):
    return an.formatar(v, 1, sufixo="%")


def resumo(medias):
    """Números da leitura: base (sem rendimento + até 1 SM) e as outras faixas, por grupo."""
    base = medias["Sem rendimento"] + medias["Mais de 0 até 1 SM"]
    return base, medias["Sem rendimento"], medias["Mais de 1 até 2 SM"], medias["Mais de 5 SM"]


# O tooltip do Altair (Vega) alinha os nomes dos campos à direita; aqui, à esquerda.
st.markdown("<style>#vg-tooltip-element td.key { text-align: left !important; }</style>",
            unsafe_allow_html=True)

# Gráfico (2/3 da largura) e, ao lado, a leitura do que ele mostra agora.
coluna_grafico, coluna_texto = st.columns([2, 1], gap="large")
coluna_grafico.altair_chart(gi.faixas_por_grupo(sel, m, agrupamento), width="stretch")

medias, contagem = an.medias_faixas(sel, agrupamento)
medias = medias[contagem > 0]
with coluna_texto:
    if len(medias) < 2:
        st.caption("A seleção cobre um só grupo de escolaridade; não há o que comparar.")
    else:
        base, sem, uma_duas, topo = resumo(medias)
        g0, g1 = medias.index[0], medias.index[-1]
        cai_sempre = bool((base.diff().dropna() < 0).all())
        st.markdown("**O que o gráfico mostra**")
        st.markdown(
            ("- **A base da renda encolhe.** " if base[g1] < base[g0] else
             "- **Nesta seleção, a base da renda não encolhe.** ")
            + f"Sem rendimento ou até 1 SM: **{pct(base[g0])}** no "
            f"{g0} e **{pct(base[g1])}** no {g1}"
            + (", caindo a cada grupo." if cai_sempre else
               " — mas não cai em todos os degraus nesta seleção.") + "\n"
            + (f"- **Quem sai da base vai sobretudo para 1 a 2 SM**, que passa de "
               f"{pct(uma_duas[g0])} para {pct(uma_duas[g1])}.\n"
               if uma_duas[g1] - uma_duas[g0] > topo[g1] - topo[g0] else "")
            + f"- **O topo muda pouco.** Mais de 5 SM vai de {pct(topo[g0])} para {pct(topo[g1])}"
            + (": mesmo no grupo mais escolarizado, menos de 1 em cada 10 ocupados."
               if topo[g1] < 10 else "."))
        st.caption("Associação entre municípios em 2010, não causa: o gráfico não diz se a "
                   "escolaridade eleva a renda ou se municípios com mais renda atraem ocupados "
                   "mais escolarizados.")

st.caption("**Passe o mouse** sobre uma faixa, na legenda ou nas barras, para destacá-la nos grupos "
           "todos e ver os valores. Fonte: Atlas do Desenvolvimento Humano no Brasil (Pnud, Ipea, "
           "FJP), Censo 2010 (IBGE).")
if filtrado and (contagem.between(1, 4)).any():
    st.caption(f"Atenção: há {nome_grupo} com menos de 5 municípios na seleção — "
               "a média dele é instável.")

# Comparação entre os três agrupamentos, sempre no estado inteiro (não depende do filtro).
with st.expander("Tercis, quartis ou quintis: o que muda ao trocar?", icon=":material/compare_arrows:"):
    linhas = []
    for nome in an.AGRUPAMENTOS:
        med_rs, _ = an.medias_faixas(ctx.mun[ctx.com_dado], nome)
        b, s_, _, t = resumo(med_rs)
        linhas.append({"Agrupamento": nome,
                       "Base no 1º grupo": pct(b.iloc[0]), "Base no último": pct(b.iloc[-1]),
                       "Diferença (p.p.)": an.formatar(b.iloc[0] - b.iloc[-1], 1),
                       "Mais de 5 SM no último": pct(t.iloc[-1]),
                       "_sem": s_})
    st.dataframe([{k: v for k, v in l.items() if k != "_sem"} for l in linhas],
                 hide_index=True, width="stretch")
    sem_q = linhas[2]["_sem"]
    st.markdown(
        "- **A conclusão é a mesma nas três opções:** a base da renda cai do grupo menos para o "
        "mais escolarizado, sem nenhuma inversão. O padrão não depende de quantos grupos são usados.\n"
        "- **Com mais grupos, as pontas se afastam.** Cada grupo extremo fica mais estreito e reúne "
        "municípios mais parecidos entre si, então a diferença entre o primeiro e o último cresce. "
        "Não é um efeito mais forte — é a mesma relação vista com mais resolução.\n"
        f"- **Os quintis mostram um detalhe que os tercis escondem:** a fatia *sem rendimento* é "
        f"quase igual no 1º e no 2º quintil ({pct(sem_q.iloc[0])} e {pct(sem_q.iloc[1])}) e só "
        f"começa a cair a partir do 3º. Nos municípios menos escolarizados, o que diminui primeiro "
        f"é quem ganha até 1 SM, não quem está sem rendimento.\n"
        "- **Mais grupos, médias mais frágeis.** Com filtro de região, quintis podem deixar grupos "
        "com poucos municípios; tercis são mais estáveis para recortes pequenos.")
    st.caption("Valores do estado inteiro (496 municípios), independentes do filtro da barra lateral.")

# ---------------------------------------------------------------------------
# Quem foge do padrão? — cada município comparado com o esperado pela escolaridade
# ---------------------------------------------------------------------------
comum.secao(
    "Quem foge do padrão?", "Atividade 02 · novo nesta atividade", "green",
    "O gráfico acima mostra médias de grupos; aqui cada município aparece sozinho. A curva "
    "tracejada é a fatia **esperada** para cada nível de escolaridade, ajustada sobre os 496 "
    "municípios; a faixa cinza vai de −1 a +1 desvio-padrão em torno dela. Quem está fora da "
    "faixa tem muito mais (ou muito menos) ocupados na faixa escolhida do que a escolaridade do "
    "município faria esperar — são os casos a investigar dentro de cada COREDE.")

coluna_alvo, coluna_mun = st.columns(2)
alvo = coluna_alvo.selectbox(
    "Faixa de renda analisada", list(an.ALVOS_P2), key="alvo_p2",
    help="A base da renda soma quem está sem rendimento e quem ganha até 1 salário mínimo. "
         "Nas faixas baixas, ficar acima do esperado é pior; em 'Mais de 5 SM', é melhor.")
nomes = sorted(sel["NM_MUN"])
if st.session_state.get("municipio_p2") not in nomes:     # saiu da seleção ao mudar o filtro
    st.session_state["municipio_p2"] = None
destaque_mun = coluna_mun.selectbox(
    "Destacar município", nomes, index=None, key="municipio_p2",
    placeholder="Escolha um município da seleção",
    help="Só aparecem os municípios que passam nos filtros da barra lateral.")

af, coef, dp = an.afastamento_p2(ctx.mun, alvo)
rotulo_alvo = alvo.split(" (")[0]
col_disp, col_rank = st.columns([1.15, 1], gap="large")
with col_disp:
    st.markdown(f"**{rotulo_alvo} × escolaridade, um ponto por município**")
    st.altair_chart(gi.dispersao_afastamento(sel, af, coef, dp, alvo, destaque_mun), width="stretch")
with col_rank:
    st.markdown("**Os 10 mais acima e os 10 mais abaixo do esperado**"
                if len(sel) > 20 else "**Municípios da seleção, do mais acima ao mais abaixo**")
    st.altair_chart(gi.ranking_afastamento(sel, af, dp, alvo, destaque_mun), width="stretch")
    st.caption("Entre parênteses, o % de ocupados com ensino médio. Faixa cinza: ±1 desvio-padrão "
               f"({an.formatar(dp, 1)} p.p.).")

if destaque_mun:
    linha = af.loc[sel.index[sel["NM_MUN"] == destaque_mun][0]]
    dif_sel = af.loc[sel.index, "diferenca"].dropna().sort_values(ascending=False)
    posicao = list(dif_sel.index).index(sel.index[sel["NM_MUN"] == destaque_mun][0]) + 1
    # Caixa neutra (em vez do azul do st.info): a página fica toda no laranja.
    st.container(border=True).markdown(
        f":material/location_on: **{destaque_mun}:** {rotulo_alvo.lower()} de **{an.formatar(linha['observado'], 1)}%** dos "
        f"ocupados; a escolaridade do município faria esperar **{an.formatar(linha['esperado'], 1)}%**. "
        f"Diferença de **{an.formatar(linha['diferenca'], 1, sinal=True)} p.p.** "
        f"({str(linha['classe']).lower()}) — {posicao}º de {len(dif_sel)} na seleção, do mais acima "
        f"para o mais abaixo do esperado.")

cores = ctx.mun[ag["coluna"]].astype(object).map(dict(zip(ag["rotulos"], cores_p2)))
legenda = [(cor, f"{g}: {an.formatar(lim[i], 1)}% a {an.formatar(lim[i + 1], 1)}%")
           for i, (g, cor) in enumerate(zip(ag["rotulos"], cores_p2))]

visiveis = ctx.mun[selecao]
tooltip = comum.tooltip_base(visiveis)
tooltip["Ensino médio"] = visiveis[ESCOLARIDADE].map(lambda v: an.formatar(v, 1, sufixo="%"))
tooltip["Grupo"] = visiveis[ag["coluna"]].astype(object).fillna("sem dado")
for coluna, nome in an.FAIXAS.items():
    tooltip[nome] = visiveis[coluna].map(lambda v: an.formatar(v, 1, sufixo="%"))

comum.secao_mapa(
    ctx, selecao, cores, legenda,
    f"Ocupados com ensino médio completo ({agrupamento.lower()} do RS)", tooltip,
    origem="novo nesta atividade",
    como_ler=("O mapa pinta cada município pelo **grupo de escolaridade** dos ocupados — os mesmos "
              "grupos do gráfico de faixas, acima, com limites calculados sobre o estado inteiro."))

tabela_p2 = sel.join(af[["observado", "esperado", "diferenca"]])
titulos_alvo = {"observado": f"{rotulo_alvo} (%)", "esperado": "Esperado (%)",
                "diferenca": "Diferença (p.p.)"}
comum.tabela(
    tabela_p2,
    {ESCOLARIDADE: "Ensino médio (%)", ag["coluna"]: ag["singular"], **titulos_alvo, **an.FAIXAS},
    ordem="diferenca", crescente=False,
    formatos={**{n: st.column_config.NumberColumn(format="%.1f")
                 for n in ["Ensino médio (%)", f"{rotulo_alvo} (%)", "Esperado (%)",
                           *an.FAIXAS.values()]},
              "Diferença (p.p.)": st.column_config.NumberColumn(format="%+.1f")},
    nota=f"Ordenada da maior diferença positiva para a maior negativa em «{rotulo_alvo}» — clique "
         "no cabeçalho para reordenar. Faixas de renda em % dos ocupados do município.",
    como_texto=[ag["singular"]])

comum.rodape()
