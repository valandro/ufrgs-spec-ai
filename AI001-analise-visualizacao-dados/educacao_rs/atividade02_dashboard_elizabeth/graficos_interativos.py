"""Gráficos interativos (Altair) criados na Atividade 02.

Diferente de `graficos_atividade01.py`, que redesenha em Matplotlib as figuras do
notebook tal como eram, aqui ficam versões que o usuário pode explorar: tooltip
com os valores e destaque de uma faixa ao passar o mouse.
"""

import altair as alt
import numpy as np
import pandas as pd

import analise as an

# Faixas mais escuras (topo da pilha) recebem rótulo branco, as claras, preto.
FAIXAS_TEXTO_BRANCO = ("Mais de 2 até 3 SM", "Mais de 3 até 5 SM", "Mais de 5 SM")


# ---------------------------------------------------------------------------
# Pergunta 1 — escolaridade × rendimento
#
# Adaptado do dashboard de `educacao/tarefa_02`: mesma dispersão, mesma reta de
# tendência, mesmo destaque de Porto Alegre e o mesmo tooltip.
#
# Uma diferença deliberada: lá a reta era reajustada a cada filtro; aqui ela é a
# do estado inteiro, vinda de `calcular()`. É a regra do dashboard — os cortes
# não mudam com o filtro — e sem ela a reta contradiria o mapa e a tabela desta
# mesma página, que medem o resíduo contra a reta dos 496 municípios.
# ---------------------------------------------------------------------------
CORES_P1 = {
    "Municípios": "#6fa3cc",
    "Porto Alegre": "#168542",
    "Reta de tendência": "#a31313",
}
TOOLTIP_P1 = [
    alt.Tooltip("NM_MUN:N", title="Município"),
    alt.Tooltip("corede:N", title="COREDE"),
    alt.Tooltip("regiao_funcional:N", title="Região Funcional"),
    alt.Tooltip("faixa_renda_sm:N", title="Faixa de renda"),
    alt.Tooltip(f"{an.ESCOLARIDADE}:Q", title="Ensino médio (%)", format=".1f"),
    alt.Tooltip(f"{an.RENDA}:Q", title="Renda (R$)", format=",.0f"),
]
EIXO_X_P1 = alt.X(f"{an.ESCOLARIDADE}:Q", title="Ocupados com ensino médio completo em 2010 (%)",
                  scale=alt.Scale(zero=False, nice=False, padding=12))
EIXO_Y_P1 = alt.Y(f"{an.RENDA}:Q", title="Rendimento médio dos ocupados (R$)",
                  scale=alt.Scale(zero=False, nice=False, padding=12))


def dispersao_escolaridade_renda(sel, modelos, destacar_poa=True):
    """Dispersão escolaridade × renda, com reta de tendência e Porto Alegre em destaque.

    `sel`: municípios da seleção, já filtrados pela página.
    `modelos`: de onde vêm a inclinação e o intercepto da reta do estado.
    `destacar_poa`: desenha Porto Alegre maior e em outra cor, quando ela está
    na seleção.
    """
    dados = sel.copy()
    dados["faixa_renda_sm"] = dados[an.RENDA].map(an.faixa_renda_sm)

    e_poa = dados["NM_MUN"].eq("Porto Alegre") if destacar_poa else pd.Series(False, index=dados.index)
    municipios = dados.loc[~e_poa].assign(tipo="Municípios")
    poa = dados.loc[e_poa].assign(tipo="Porto Alegre")

    # A reta é a do estado (496 municípios), desenhada só até onde a seleção vai.
    x0, x1 = float(dados[an.ESCOLARIDADE].min()), float(dados[an.ESCOLARIDADE].max())
    reta = pd.DataFrame({
        an.ESCOLARIDADE: [x0, x1],
        an.RENDA: [modelos.p1_intercepto + modelos.p1_inclinacao * x
                   for x in (x0, x1)],
        "tipo": "Reta de tendência",
    })

    # A legenda só lista o que está desenhado: sem Porto Alegre na seleção, a
    # entrada dela não aparece.
    presentes = ["Municípios"] + (["Porto Alegre"] if not poa.empty else []) + ["Reta de tendência"]
    cor = alt.Color("tipo:N", title="Elementos do gráfico",
                    scale=alt.Scale(domain=presentes, range=[CORES_P1[t] for t in presentes]),
                    legend=alt.Legend(orient="top", direction="horizontal"))

    camadas = [
        alt.Chart(municipios).mark_circle(size=55, opacity=0.65).encode(
            x=EIXO_X_P1, y=EIXO_Y_P1, color=cor, tooltip=TOOLTIP_P1),
        alt.Chart(reta).mark_line(size=3).encode(x=EIXO_X_P1, y=EIXO_Y_P1, color=cor),
    ]
    if not poa.empty:
        # Depois da reta, para o marcador da capital não ficar por baixo dela.
        camadas.append(alt.Chart(poa).mark_circle(size=180, opacity=1).encode(
            x=EIXO_X_P1, y=EIXO_Y_P1, color=cor, tooltip=TOOLTIP_P1))

    return alt.layer(*camadas).properties(height=460).configure_axis(
        grid=True, gridColor="#e5e5e0")


def faixas_por_grupo(sel, modelos, agrupamento=an.AGRUPAMENTO_PADRAO):
    """Barras 100% empilhadas das faixas de renda por grupo de escolaridade (pergunta 2).

    Interações:
    - passar o mouse sobre uma faixa — na legenda ou na barra — destaca essa
      faixa nos grupos todos e esmaece as demais;
    - o tooltip mostra grupo, intervalo de escolaridade, n e o % médio da faixa.
    """
    ag = an.AGRUPAMENTOS[agrupamento]
    medias, contagem = an.medias_faixas(sel, agrupamento)
    lim = modelos.p2_limites[agrupamento]
    grupos = [g for g in ag["rotulos"] if contagem[g] > 0]
    faixas = list(medias.columns)                     # da base para o topo da pilha

    # Formato longo: uma linha por (grupo, faixa), como o Altair espera.
    linhas = []
    for g in grupos:
        i = ag["rotulos"].index(g)
        intervalo = f"{an.formatar(lim[i], 1)}% a {an.formatar(lim[i + 1], 1)}%"
        acumulado = 0.0
        for ordem, faixa in enumerate(faixas):
            v = float(medias.loc[g, faixa])
            linhas.append({
                "grupo": g,
                # rótulo do eixo em 3 linhas, separadas por "|" (quebradas no labelExpr)
                "rotulo": f"{g}|({an.formatar(lim[i], 1)}–{an.formatar(lim[i + 1], 1)}%)|n = {contagem[g]}",
                "intervalo": intervalo,
                "n": int(contagem[g]),
                "faixa": faixa,
                "ordem": ordem,
                "pct": v,
                "pct_txt": an.formatar(v, 1, sufixo="%"),
                "meio": acumulado + v / 2,                # centro do segmento, para o rótulo
            })
            acumulado += v
    dados = pd.DataFrame(linhas)
    ordem_x = [dados.loc[dados["grupo"] == g, "rotulo"].iloc[0] for g in grupos]

    destaque = alt.selection_point(
        fields=["faixa"], on="mouseover", clear="mouseout",
        bind=alt.LegendStreamBinding(legend="mouseover"))
    opacidade = alt.condition(destaque, alt.value(1), alt.value(0.25))

    base = alt.Chart(dados).encode(
        x=alt.X("rotulo:N", sort=ordem_x,
                title=f"{ag['singular']} de % de ocupados com ensino médio completo (mesmo n por grupo)",
                axis=alt.Axis(labelAngle=0, labelLimit=0, labelFontSize=11, labelOverlap=False,
                              labelExpr="split(datum.label, '|')")),
    )

    # Traço branco entre os segmentos: separa faixas vizinhas de tom parecido.
    barras = base.mark_bar(size=62 if len(grupos) <= 4 else 52, stroke="white", strokeWidth=1).encode(
        y=alt.Y("pct:Q", stack="zero", scale=alt.Scale(domain=[0, 100]),
                title="Ocupados por faixa de rendimento (%)"),
        # Domínio invertido: a legenda lista de cima para baixo, na ordem da pilha.
        color=alt.Color("faixa:N", scale=alt.Scale(domain=faixas[::-1], range=an.CORES_FAIXAS_P2[::-1]),
                        legend=alt.Legend(title="Faixa de rendimento", orient="right")),
        order=alt.Order("ordem:Q"),                   # "Sem rendimento" na base
        opacity=opacidade,
        tooltip=[alt.Tooltip("grupo:N", title=ag["singular"]),
                 alt.Tooltip("intervalo:N", title="Ensino médio completo"),
                 alt.Tooltip("n:Q", title="Municípios"),
                 alt.Tooltip("faixa:N", title="Faixa de renda"),
                 alt.Tooltip("pct_txt:N", title="% médio dos ocupados")],
    ).add_params(destaque)

    # Rótulo em cada fatia de 5% ou mais, como no gráfico do notebook.
    rotulos = base.transform_filter("datum.pct >= 5").transform_calculate(
        texto="format(datum.pct, '.0f') + '%'"
    ).mark_text(fontSize=11).encode(
        y=alt.Y("meio:Q"),
        text="texto:N",
        color=alt.condition(alt.FieldOneOfPredicate(field="faixa", oneOf=list(FAIXAS_TEXTO_BRANCO)),
                            alt.value("white"), alt.value("#0b0b0b")),
        opacity=opacidade,
    )

    # Largura: a do contêiner (st.altair_chart com width="stretch"); as barras
    # mantêm a espessura fixa acima, então mais grupos só ocupam mais espaço.
    return (barras + rotulos).properties(height=420).configure_view(stroke=None).configure_axis(grid=False)


# ---------------------------------------------------------------------------
# Pergunta 2 — "Quem foge do padrão?"
# ---------------------------------------------------------------------------
# Rampa laranja da pergunta 2 (a dos quartis), do claro (abaixo do esperado) ao
# escuro (acima), na ordem de an.CLASSES_P2.
CORES_AFASTAMENTO = ["#eba186", "#cd7352", "#ae4417", "#7c2800"]
COR_DESTAQUE = "#1a1a1a"


def _pontos_afastamento(sel, af):
    """Tabela dos municípios da seleção com os textos já formatados para o tooltip."""
    d = sel[["NM_MUN", "corede", an.ESCOLARIDADE]].join(af).dropna(subset=["diferenca"])
    d = d.rename(columns={"NM_MUN": "municipio", an.ESCOLARIDADE: "escolaridade"})
    d["classe"] = d["classe"].astype(str)
    d["esc_txt"] = d["escolaridade"].map(lambda v: an.formatar(v, 1, sufixo="%"))
    d["obs_txt"] = d["observado"].map(lambda v: an.formatar(v, 1, sufixo="%"))
    d["esp_txt"] = d["esperado"].map(lambda v: an.formatar(v, 1, sufixo="%"))
    d["dif_txt"] = d["diferenca"].map(lambda v: an.formatar(v, 1, sinal=True, sufixo=" p.p."))
    return d


def _tooltip_afastamento(rotulo_alvo):
    return [alt.Tooltip("municipio:N", title="Município"),
            alt.Tooltip("corede:N", title="COREDE"),
            alt.Tooltip("esc_txt:N", title="Ensino médio completo"),
            alt.Tooltip("obs_txt:N", title=f"{rotulo_alvo} (observado)"),
            alt.Tooltip("esp_txt:N", title="Esperado pela escolaridade"),
            alt.Tooltip("dif_txt:N", title="Diferença"),
            alt.Tooltip("classe:N", title="Classe")]


def dispersao_afastamento(sel, af, coef, dp, alvo, destaque=None):
    """Um ponto por município: escolaridade × fatia da faixa `alvo`, com a curva esperada e ±1 dp."""
    d = _pontos_afastamento(sel, af)
    rotulo = alvo.split(" (")[0]
    cor = alt.Color("classe:N", scale=alt.Scale(domain=an.CLASSES_P2, range=CORES_AFASTAMENTO),
                    legend=alt.Legend(title=None, orient="bottom", direction="vertical", labelLimit=0))

    xs = np.linspace(float(d["escolaridade"].min()), float(d["escolaridade"].max()), 80)
    curva = pd.DataFrame({"escolaridade": xs, "esperado": an.curva_p2(coef, xs)})
    curva["baixo"] = (curva["esperado"] - dp).clip(lower=0)
    curva["alto"] = curva["esperado"] + dp

    x = alt.X("escolaridade:Q", title="Ocupados com ensino médio completo (%)", scale=alt.Scale(zero=False))
    faixa = alt.Chart(curva).mark_area(color="#52514e", opacity=0.09).encode(
        x=x, y="baixo:Q", y2="alto:Q")
    linha = alt.Chart(curva).mark_line(color="#52514e", strokeDash=[6, 4], strokeWidth=2).encode(
        x=x, y="esperado:Q")
    pontos = alt.Chart(d).mark_circle(size=34, opacity=0.9).encode(
        x=x, y=alt.Y("observado:Q", title=f"{rotulo} (% dos ocupados)"),
        color=cor, tooltip=_tooltip_afastamento(rotulo))
    camadas = faixa + linha + pontos
    if destaque is not None and destaque in set(d["municipio"]):
        dd = d[d["municipio"] == destaque]
        camadas += alt.Chart(dd).mark_point(size=260, shape="circle", filled=False,
                                            color=COR_DESTAQUE, strokeWidth=2.5).encode(
            x=x, y="observado:Q", tooltip=_tooltip_afastamento(rotulo))
        camadas += alt.Chart(dd).mark_text(align="left", dx=12, dy=-10, fontSize=12,
                                           fontWeight="bold", color=COR_DESTAQUE).encode(
            x=x, y="observado:Q", text="municipio:N")
    return camadas.properties(height=430)


def ranking_afastamento(sel, af, dp, alvo, destaque=None, n=10):
    """Os `n` municípios da seleção mais acima e os `n` mais abaixo do esperado.

    O município em destaque entra no ranking mesmo fora das pontas, com contorno.
    """
    d = _pontos_afastamento(sel, af).sort_values("diferenca")
    d["posicao"] = np.arange(len(d), 0, -1)                   # 1 = mais acima do esperado
    if len(d) <= 2 * n:
        r = d
    else:
        r = pd.concat([d.head(n), d.tail(n)])
        if destaque is not None and destaque in set(d["municipio"]) and destaque not in set(r["municipio"]):
            r = pd.concat([r, d[d["municipio"] == destaque]]).sort_values("diferenca")
    r = r.copy()
    r["rotulo"] = r.apply(lambda l: ("▶ " if l["municipio"] == destaque else "")
                          + f"{l['municipio']} ({an.formatar(l['escolaridade'], 0)}%)", axis=1)
    r["lado"] = np.where(r["diferenca"] > 0, "Acima do esperado", "Abaixo do esperado")
    r["e_destaque"] = r["municipio"] == destaque
    r["valor_txt"] = r["diferenca"].map(lambda v: an.formatar(v, 0, sinal=True))
    ordem_y = list(r.sort_values("diferenca", ascending=False)["rotulo"])
    rotulo = alvo.split(" (")[0]

    y = alt.Y("rotulo:N", sort=ordem_y, title=None,
              axis=alt.Axis(labelLimit=240, labelOverlap=False))
    limite = float(max(abs(r["diferenca"]).max(), dp)) * 1.18
    x = alt.X("diferenca:Q", title="Diferença para o esperado (p.p.)",
              scale=alt.Scale(domain=[-limite, limite]))

    # Faixa cinza: ±1 desvio-padrão, a zona "dentro do esperado".
    zona = alt.Chart(pd.DataFrame({"diferenca": [-dp], "b": [dp]})).mark_rect(
        color="#52514e", opacity=0.07).encode(x=x, x2="b:Q")
    barras = alt.Chart(r).mark_bar(height={"band": 0.72}).encode(
        x=x, y=y,
        color=alt.Color("lado:N", scale=alt.Scale(domain=["Abaixo do esperado", "Acima do esperado"],
                                                   range=[CORES_AFASTAMENTO[0], CORES_AFASTAMENTO[3]]),
                        legend=None),
        stroke=alt.condition("datum.e_destaque", alt.value(COR_DESTAQUE), alt.value(None)),
        strokeWidth=alt.condition("datum.e_destaque", alt.value(2.5), alt.value(0)),
        tooltip=_tooltip_afastamento(rotulo) + [alt.Tooltip("posicao:Q", title="Posição na seleção")])
    # Valor na ponta de cada barra: à direita das positivas, à esquerda das negativas.
    texto = dict(x=x, y=y, text="valor_txt:N")
    valores = (alt.Chart(r).transform_filter("datum.diferenca > 0")
               .mark_text(fontSize=11, align="left", dx=4).encode(**texto)
               + alt.Chart(r).transform_filter("datum.diferenca <= 0")
               .mark_text(fontSize=11, align="right", dx=-4).encode(**texto))
    zero = alt.Chart(pd.DataFrame({"diferenca": [0]})).mark_rule(color="#52514e").encode(x=x)
    return (zona + barras + valores + zero).properties(height=max(22 * len(r), 200))
