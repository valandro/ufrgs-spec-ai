"""Gráficos da Atividade 01, no mesmo modelo de `notebook/atividade01_dados_pib_2010.ipynb`.

Cada função reproduz um gráfico da seção 6 daquele notebook — mesmas cores,
títulos, eixos, anotações e rodapé de fontes. A única adaptação é o destaque
da seleção feita nos filtros do dashboard:

- as estatísticas (retas, medianas, quartis, p-valores) continuam calculadas
  sobre os 496 municípios, como na Atividade 01;
- os municípios fora da seleção ficam em cinza, e os de dentro mantêm as
  cores originais.

Com todas as regiões marcadas, cada figura é a mesma da Atividade 01.

As figuras são criadas com `matplotlib.figure.Figure`, e não com `pyplot`,
porque o Streamlit atende várias sessões em paralelo e o estado global do
pyplot não é seguro entre elas.
"""

import numpy as np
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.ticker import NullFormatter, ScalarFormatter

import analise as an
from analise import ESCOLARIDADE, PIB, POPULACAO, RENDA

COR_FORA = "#dcdbd5"
FONTE_ATLAS = ("Fonte: Atlas do Desenvolvimento Humano no Brasil (Pnud, Ipea, FJP), "
               "com dados do Censo 2010 (IBGE).")


def _reais(valor):
    return f"R\\$ {valor:,.0f}".replace(",", ".")


def _estilo(ax, grade="y"):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis=grade, linestyle="-", linewidth=0.5, color="#e5e5e0", zorder=0)
    ax.set_axisbelow(True)


# ---------------------------------------------------------------------------
# 6.1 — Pergunta 1
# ---------------------------------------------------------------------------
def grafico_6_1(mun, modelos, selecao):
    """Dispersão escolaridade × rendimento com reta de tendência e r de Pearson."""
    COR_PONTOS = "#2a78d6"
    COR_LINHA = "#52514e"
    base = mun[mun[RENDA].notna()]
    dentro = selecao[base.index]
    filtrado = not dentro.all()

    fig = Figure(figsize=(8, 6))
    ax = fig.subplots()
    if filtrado:
        fora = base[~dentro]
        ax.scatter(fora[ESCOLARIDADE], fora[RENDA], s=18, color=COR_FORA, alpha=0.8,
                   edgecolors="none", label=f"Demais municípios do RS (n={len(fora)})")
    escolhidos = base[dentro]
    ax.scatter(escolhidos[ESCOLARIDADE], escolhidos[RENDA], s=22, color=COR_PONTOS, alpha=0.6,
               edgecolors="none",
               label=(f"Seleção (n={len(escolhidos)})" if filtrado
                      else f"Municípios do RS (n={len(escolhidos)})"))

    x_linha = np.array([base[ESCOLARIDADE].min(), base[ESCOLARIDADE].max()])
    ax.plot(x_linha, modelos.p1_inclinacao * x_linha + modelos.p1_intercepto, color=COR_LINHA,
            linewidth=2, linestyle="--", label="Tendência linear")

    ax.set_title("Municípios com mais trabalhadores com ensino médio completo\n"
                 "pagam salários mais altos?", fontsize=13, pad=12)
    ax.set_xlabel("Ocupados com ensino médio completo (%)")
    ax.set_ylabel("Rendimento médio dos ocupados (R\\$, 2010)")
    _estilo(ax)
    ax.annotate(f"r de Pearson = {modelos.p1_r:.2f}", xy=(0.03, 0.94), xycoords="axes fraction",
                fontsize=10, color=COR_LINHA)
    ax.legend(frameon=False, loc="lower right")
    fig.text(0.01, 0.005, FONTE_ATLAS + ("\nReta e r calculados sobre os 496 municípios; "
                                         "os filtros só destacam a seleção." if filtrado else ""),
             fontsize=8, color="#8a8a86")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    return fig


# ---------------------------------------------------------------------------
# 6.2.1 — Pergunta 2
# ---------------------------------------------------------------------------
# Modelo: célula 6.2.1 de `notebook/atividade01_versao_final.ipynb` — barras 100%
# empilhadas, rampa sequencial de um tom, rótulo em cada fatia de 5% ou mais,
# legenda à direita na ordem da pilha (topo primeiro), figura de 8 × 6 — com os
# quartis (pd.qcut) descritos no título da seção e interpretados em 6.2.2.
FAIXAS_TEXTO_BRANCO = ("Mais de 2 até 3 SM", "Mais de 3 até 5 SM", "Mais de 5 SM")


def _barras_faixas(medias, rotulos_x, titulo, xlabel, rodape):
    CORES_SEQUENCIAIS = an.CORES_FAIXAS
    fig = Figure(figsize=(8, 6))
    ax = fig.subplots()
    x = np.arange(len(medias))
    base = np.zeros(len(medias))
    for faixa, cor in zip(medias.columns, CORES_SEQUENCIAIS):
        valores = medias[faixa].to_numpy()
        ax.bar(x, valores, bottom=base, color=cor, width=0.6, label=faixa)
        for i, v in enumerate(valores):
            if v >= 5:
                ax.text(x[i], base[i] + v / 2, f"{v:.0f}%", ha="center", va="center", fontsize=9,
                        color="white" if faixa in FAIXAS_TEXTO_BRANCO else "#0b0b0b")
        base += valores
    ax.set_xticks(x)
    ax.set_xticklabels(rotulos_x)
    ax.set_ylim(0, 100)
    ax.set_title(titulo, fontsize=13, pad=12)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Ocupados por faixa de rendimento (%)")
    ax.spines[["top", "right"]].set_visible(False)
    ax.set_axisbelow(True)
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], frameon=False, loc="center left",
              bbox_to_anchor=(1.02, 0.5), fontsize=9)
    linhas = rodape.count("\n") + 1
    fig.text(0.01, 0.005, rodape, fontsize=8, color="#8a8a86")
    fig.tight_layout(rect=(0, 0.03 * linhas, 1, 1))
    return fig


def _rodape_p2(filtrado):
    texto = (FONTE_ATLAS + "\nFaixas de renda convertidas de cumulativas para mutuamente "
             "exclusivas; cada barra é a média das distribuições municipais.")
    if filtrado:
        texto += ("\nLimites dos quartis calculados sobre os 496 municípios; barras com a média "
                  "dos municípios da seleção.")
    return texto


def grafico_6_2(sel, modelos, filtrado):
    """Versão em quartis — a usada como resposta da pergunta 2 (interpretação 6.2.2)."""
    medias, contagem = an.medias_faixas(sel)
    quartis = [q for q in an.QUARTIS if contagem[q] > 0]
    lim = modelos.p2_limites
    rotulos = []
    for q in quartis:
        i = an.QUARTIS.index(q)
        rotulos.append(f"{q}\n({lim[i]:.1f}% – {lim[i + 1]:.1f}%)\n(n={contagem[q]})")
    return _barras_faixas(
        medias.loc[quartis], rotulos,
        "Como muda a distribuição de faixas de renda\nconforme o nível de escolaridade do "
        "município? (quartis)" + (f"\nSeleção: {len(sel)} municípios" if filtrado else ""),
        "Quartil de % de ocupados com ensino médio completo (mesmo n por grupo)",
        _rodape_p2(filtrado))


# ---------------------------------------------------------------------------
# 6.3.2 — Pergunta 3
# ---------------------------------------------------------------------------
def grafico_6_3(mun, selecao, rfs):
    """Renda por Região Funcional: caixa + um ponto por município, RF1 em destaque."""
    COR_METRO = "#eb6834"
    COR_DEMAIS = "#2a78d6"
    base = mun[mun[RENDA].notna()]
    dentro = selecao[base.index]
    resumo = base.groupby("regiao_funcional")[RENDA].agg(n="size", mediana="median")
    resumo = resumo.sort_values("mediana", ascending=False)
    posicao_rf1 = resumo.index.get_loc("RF1 · Metropolitana") + 1
    ordem = resumo.index.tolist()[::-1]      # maior mediana no topo
    rng_jitter = np.random.default_rng(3)

    fig = Figure(figsize=(11, 6.8))
    ax = fig.subplots()
    for i, nome_rf in enumerate(ordem):
        da_rf = base["regiao_funcional"] == nome_rf
        valores = base.loc[da_rf, RENDA]
        cor = COR_METRO if nome_rf.startswith("RF1") else COR_DEMAIS
        if nome_rf not in rfs:
            cor = COR_FORA
        ax.boxplot([valores], positions=[i], vert=False, widths=0.62, showfliers=False,
                   patch_artist=True,
                   boxprops=dict(facecolor="white", edgecolor=cor, linewidth=1.3),
                   medianprops=dict(color=cor, linewidth=2.6),
                   whiskerprops=dict(color=cor, linewidth=1.1),
                   capprops=dict(color=cor, linewidth=1.1))
        y = i + rng_jitter.uniform(-0.17, 0.17, len(valores))
        cores_pontos = np.where(dentro[da_rf].to_numpy(), cor, COR_FORA)
        alfas = np.where(dentro[da_rf].to_numpy(), 0.35, 0.25)
        ax.scatter(valores, y, s=11, c=cores_pontos, alpha=alfas, edgecolors="none", zorder=3)
        ax.annotate(_reais(valores.median()), xy=(valores.median(), i + 0.40), ha="center",
                    fontsize=8.5, color=cor, fontweight="bold")

    mediana_estado = base[RENDA].median()
    ax.axvline(mediana_estado, color="#8a8a86", linestyle=":", linewidth=1.2, zorder=1)
    ax.annotate(f"mediana do estado: {_reais(mediana_estado)}", xy=(mediana_estado, -0.78),
                xytext=(8, 0), textcoords="offset points", fontsize=8.5, color="#8a8a86",
                va="center")
    ax.set_yticks(range(len(ordem)))
    ax.set_yticklabels([f"{nome}  (n={resumo.loc[nome, 'n']})" for nome in ordem], fontsize=9.5)
    ax.set_ylim(-1.15, len(ordem) - 0.35)
    ax.set_xlabel("Rendimento médio dos ocupados (R\\$, 2010)")
    ax.set_title("A proximidade da capital explica o rendimento?\n"
                 f"Os {len(base)} municípios do RS por Região Funcional de Planejamento — "
                 f"a metropolitana é a {posicao_rf1}ª de {len(resumo)}", fontsize=13, pad=12)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="x", linestyle="-", linewidth=0.5, color="#e5e5e0", zorder=0)
    ax.set_axisbelow(True)
    ax.legend(handles=[
        Line2D([], [], color=COR_METRO, linewidth=2.6, label="Região Funcional 1 (metropolitana)"),
        Line2D([], [], color=COR_DEMAIS, linewidth=2.6, label="Demais Regiões Funcionais"),
    ], frameon=False, loc="lower right", fontsize=9)
    filtrado = not dentro.all()
    fig.text(0.01, 0.005,
             "Fontes: Atlas do Desenvolvimento Humano no Brasil (Pnud, Ipea, FJP), Censo 2010 (IBGE); "
             "Regiões Funcionais de Planejamento — Decreto 54.572/2019 (SEPLAG-RS).\n"
             "Caixa = 1º ao 3º quartil; linha grossa = mediana; cada ponto é um município. "
             "Outliers omitidos da caixa para não duplicar os pontos já desenhados."
             + ("\nCaixas e medianas de cada região com todos os seus municípios; em cinza, "
                "regiões e municípios fora da seleção." if filtrado else ""),
             fontsize=8, color="#8a8a86")
    fig.tight_layout(rect=(0, 0.08 if filtrado else 0.06, 1, 1))
    return fig


# ---------------------------------------------------------------------------
# 6.4.2 — Pergunta 4
# ---------------------------------------------------------------------------
def grafico_6_4_2(mun, modelos, selecao):
    """Dispersão PIB per capita × rendimento com a renda esperada e ± 1 desvio-padrão."""
    COR_BASE = "#c2d4e8"
    COR_RETA = "#52514e"
    COR_ACIMA = "#eb6834"
    COR_ABAIXO = "#2a78d6"
    base = mun[mun[RENDA].notna()].assign(pib_pc_mil=lambda d: d[PIB] / 1000)
    dentro = selecao[base.index]
    filtrado = not dentro.all()
    corte = modelos.p4_corte_tercil / 1000
    dp = modelos.p4_dp

    fig = Figure(figsize=(11.5, 6.8))
    ax = fig.subplots()
    ax.axvspan(base["pib_pc_mil"].min() * 0.92, corte, color="#f2f2ee", zorder=0)
    ax.annotate("tercil inferior de PIB per capita — recorte da 2ª metade da pergunta",
                xy=(0.012, 0.015), xycoords="axes fraction", fontsize=8.5, color="#8a8a86",
                va="bottom")

    if filtrado:
        # O azul-claro original some contra o cinza; na seleção ele escurece um tom.
        COR_BASE = "#8fb3dc"
        fora = base[~dentro]
        ax.scatter(fora["pib_pc_mil"], fora[RENDA], s=14, color="#e6e5e0", alpha=0.9,
                   edgecolors="none", zorder=2, label=f"Fora da seleção (n={len(fora)})")
    escolhidos = base[dentro]
    ax.scatter(escolhidos["pib_pc_mil"], escolhidos[RENDA], s=16, color=COR_BASE, alpha=0.9,
               edgecolors="none", zorder=2,
               label=(f"Seleção (n={len(escolhidos)})" if filtrado
                      else f"Municípios do RS (n={len(escolhidos)})"))

    grade = np.logspace(np.log10(base["pib_pc_mil"].min()), np.log10(base["pib_pc_mil"].max()), 200)
    esperado = modelos.p4_intercepto + modelos.p4_inclinacao * np.log10(grade)
    ax.plot(grade, esperado, color=COR_RETA, linewidth=2.2, zorder=5,
            label="Renda esperada pelo PIB per capita")
    for sinal in (+1, -1):
        ax.plot(grade, esperado + sinal * dp, color=COR_RETA, linewidth=1.1, linestyle="--",
                zorder=4, label="± 1 desvio-padrão do resíduo" if sinal == 1 else None)

    grupo_alto = escolhidos[escolhidos["destaque_p4"]]
    ax.scatter(grupo_alto["pib_pc_mil"], grupo_alto[RENDA], s=62, color=COR_ACIMA, zorder=6,
               edgecolors="white", linewidth=0.9,
               label=f"PIB baixo, renda acima do esperado (n={len(grupo_alto)})")
    abaixo = escolhidos[escolhidos["residuo_p4"] < -dp]
    ax.scatter(abaixo["pib_pc_mil"], abaixo[RENDA], s=26, color=COR_ABAIXO, alpha=0.75, zorder=3,
               edgecolors="none", label=f"Produzem muito, renda baixa (n={len(abaixo)})")

    # Mesmos rótulos da Atividade 01, só para os municípios que estão na seleção.
    ROTULOS_ACIMA = ["Pelotas", "Bagé", "Uruguaiana", "Viamão", "Alvorada"]
    posicao = 0
    for nome_mun in ROTULOS_ACIMA:
        linha = escolhidos[escolhidos["NM_MUN"] == nome_mun]
        if linha.empty:
            continue
        ax.annotate(nome_mun, xy=(linha["pib_pc_mil"].iloc[0], linha[RENDA].iloc[0]),
                    xytext=(0.045, 0.95 - posicao * 0.055), textcoords="axes fraction",
                    fontsize=8.5, color=COR_ACIMA, zorder=7, va="center",
                    arrowprops=dict(arrowstyle="-", color=COR_ACIMA, linewidth=0.7,
                                    shrinkA=2, shrinkB=3, alpha=0.7))
        posicao += 1
    for nome_mun, deslocamento in {"Triunfo": (-46, 12), "Pinhal da Serra": (-34, -18),
                                   "Capão do Cipó": (-42, -18)}.items():
        linha = escolhidos[escolhidos["NM_MUN"] == nome_mun]
        if not linha.empty:
            ax.annotate(nome_mun, xy=(linha["pib_pc_mil"].iloc[0], linha[RENDA].iloc[0]),
                        xytext=deslocamento, textcoords="offset points", fontsize=8.5,
                        color=COR_ABAIXO, zorder=7)

    ax.set_xscale("log")
    ax.set_xticks([7, 10, 15, 25, 40, 70, 120, 220])
    ax.get_xaxis().set_major_formatter(ScalarFormatter())
    ax.get_xaxis().set_minor_formatter(NullFormatter())
    ax.set_xlabel("PIB per capita em 2010 (R\\$ mil por habitante, escala log)")
    ax.set_ylabel("Rendimento médio dos ocupados (R\\$, 2010)")
    acima_rs = int((base["residuo_p4"] > dp).sum())
    abaixo_rs = int((base["residuo_p4"] < -dp).sum())
    ax.set_title("Existem municípios cuja renda é incompatível com a produção local?\n"
                 f"{acima_rs} ganham muito mais do que produzem; "
                 f"{abaixo_rs} produzem muito e a renda não fica com os residentes",
                 fontsize=13, pad=12)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle="-", linewidth=0.5, color="#e5e5e0", zorder=1)
    ax.legend(frameon=False, loc="upper right", fontsize=8.5)
    fig.text(0.01, 0.005,
             "Fontes: Atlas do Desenvolvimento Humano no Brasil (Pnud, Ipea, FJP), Censo 2010 (IBGE); "
             "PIB dos municípios 2010 (IBGE).\n"
             "Renda esperada = ajuste de mínimos quadrados do rendimento contra o log do PIB per capita. "
             "Resíduo = renda observada − renda esperada."
             + ("\nReta, faixa e contagens do título calculadas sobre os 496 municípios; "
                "os filtros só destacam a seleção." if filtrado else ""),
             fontsize=8, color="#8a8a86")
    fig.tight_layout(rect=(0, 0.07 if filtrado else 0.055, 1, 1))
    return fig


# ---------------------------------------------------------------------------
# 6.4.3 — Pergunta 4
# ---------------------------------------------------------------------------
def grafico_6_4_3(mun, modelos, selecao, p_valores):
    """Os dois grupos do tercil inferior de PIB comparados em quatro indicadores."""
    COR_ACIMA = "#eb6834"
    COR_RESTO = "#7fa8d4"
    CLASSES = {False: "Renda compatível com o PIB", True: "Renda acima do esperado"}
    CORES = {False: COR_RESTO, True: COR_ACIMA}
    PAINEIS = [
        (ESCOLARIDADE, "Ocupados com ensino médio completo (%)", False),
        (POPULACAO, "População em 2010 (habitantes, escala log)", True),
        ("pct_vab_servicos_2010", "Serviços no valor adicionado (%)", False),
        ("pct_vab_agropecuaria_2010", "Agropecuária no valor adicionado (%)", False),
    ]
    baixo = mun[mun["tercil_inferior_pib"]]
    dentro = selecao[baixo.index].to_numpy()
    filtrado = not selecao[mun[RENDA].notna()].all()
    rng_jitter = np.random.default_rng(5)

    fig = Figure(figsize=(12.5, 8))
    axes = fig.subplots(2, 2)
    for ax, (coluna, rotulo, usar_log) in zip(axes.ravel(), PAINEIS):
        for i, alto in enumerate((False, True)):
            do_grupo = (baixo["destaque_p4"] == alto).to_numpy()
            valores = baixo.loc[do_grupo, coluna]
            y = i + rng_jitter.uniform(-0.17, 0.17, len(valores))
            cores = np.where(dentro[do_grupo], CORES[alto], COR_FORA)
            ax.scatter(valores, y, s=28, c=cores, alpha=0.6, edgecolors="none", zorder=3)
            mediana = valores.median()
            ax.plot([mediana, mediana], [i - 0.33, i + 0.33], color=CORES[alto], linewidth=3, zorder=5)
            texto = f"{mediana:,.0f}".replace(",", ".") if usar_log else f"{mediana:.1f}"
            ax.annotate(texto, xy=(mediana, i + 0.42), ha="center", fontsize=9, color=CORES[alto],
                        fontweight="bold")
        if usar_log:
            ax.set_xscale("log")
        p = p_valores[coluna]
        texto_p = "p < 0,0001" if p < 0.0001 else f"p = {p:.4f}".replace(".", ",")
        ax.set_title(texto_p, fontsize=10, pad=6, color="#52514e" if p < 0.05 else "#a8a8a3")
        ax.set_yticks([0, 1])
        ax.set_yticklabels([f"{CLASSES[a]}\n(n={int((baixo['destaque_p4'] == a).sum())})"
                            for a in (False, True)], fontsize=9)
        ax.set_ylim(-0.65, 1.8)
        ax.set_xlabel(rotulo, fontsize=9.5)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.grid(axis="x", linestyle="-", linewidth=0.5, color="#e5e5e0", zorder=0)
        ax.set_axisbelow(True)

    corte = f"{modelos.p4_corte_tercil:,.0f}".replace(",", ".")
    fig.suptitle("Entre municípios que produzem o mesmo por habitante, o que distingue os de renda alta?\n"
                 f"Tercil inferior de PIB per capita (≤ R\\$ {corte}/hab.) — {len(baixo)} municípios",
                 fontsize=13.5)
    p_adm = p_valores["pct_vab_adm_publica_2010"]
    fig.text(0.01, 0.005,
             "Fontes: Atlas do Desenvolvimento Humano no Brasil (Pnud, Ipea, FJP), Censo 2010 (IBGE); "
             "PIB dos municípios 2010 (IBGE).\n"
             "Barra vertical = mediana do grupo; cada ponto é um município. p = teste de permutação da "
             "diferença de medianas (20.000 reamostras).\n"
             f"A administração pública é o único candidato testado que NÃO distingue os grupos "
             f"(p = {p_adm:.2f}).".replace("0.", "0,")
             + ("\nGrupos, medianas e p-valores com os 166 municípios do tercil; em cinza, os "
                "municípios fora da seleção." if filtrado else ""),
             fontsize=8, color="#8a8a86")
    fig.tight_layout(rect=(0, 0.09 if filtrado else 0.07, 1, 1))
    return fig
