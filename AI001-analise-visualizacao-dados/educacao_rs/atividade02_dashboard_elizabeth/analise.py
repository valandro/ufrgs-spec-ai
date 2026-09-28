"""Cálculos das 4 perguntas da Atividade 01, separados da interface.

Tudo o que depende de um corte estatístico — retas, tercis, quintis,
desvios-padrão, tercil de PIB — é calculado UMA vez, sobre os 496 municípios
com dado em 2010. Os filtros do dashboard só escolhem o que aparece; nunca
recalculam os cortes. Assim um município mantém sempre a mesma classe, e os
números batem com os notebooks da Atividade 01.

Rodar `python analise.py` confere os resultados contra os valores publicados
em `notebook/atividade01_dados_pib_2010.ipynb`.
"""

from dataclasses import dataclass
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

PASTA_DADOS = Path(__file__).parent / "dados"
ARQUIVO_MUNICIPIOS = PASTA_DADOS / "municipios_web.geojson"
ARQUIVO_REGIOES = PASTA_DADOS / "regioes_web.geojson"

RENDA = "rendimento_ocupados_2010"
ESCOLARIDADE = "pct_ocupados_ensino_medio_2010"
PIB = "pib_per_capita_2010"
POPULACAO = "populacao_2010"
DISTANCIA = "dist_poa_km"

# Seis faixas mutuamente exclusivas (pergunta 2), na ordem de empilhamento.
FAIXAS = {
    "pct_sem_rendimento_2010": "Sem rendimento",
    "pct_ate_1sm_2010": "Mais de 0 até 1 SM",
    "pct_1a2sm_2010": "Mais de 1 até 2 SM",
    "pct_2a3sm_2010": "Mais de 2 até 3 SM",
    "pct_3a5sm_2010": "Mais de 3 até 5 SM",
    "pct_mais_5sm_2010": "Mais de 5 SM",
}
SETORES = {
    "pct_vab_agropecuaria_2010": "Agropecuária",
    "pct_vab_industria_2010": "Indústria",
    "pct_vab_servicos_2010": "Serviços",
    "pct_vab_adm_publica_2010": "Adm. pública",
}

# Pergunta 2 — três formas de agrupar os municípios pela escolaridade. As três são
# calculadas em `calcular()`, sobre os 496 municípios; o dashboard só escolhe qual mostrar.
# Todas usam pd.qcut: cada grupo tem (quase) o mesmo número de municípios.
AGRUPAMENTOS = {
    "Tercis": {"singular": "Tercil", "n": 3, "coluna": "tercil_esc", "rotulos": ["T1", "T2", "T3"]},
    "Quartis": {"singular": "Quartil", "n": 4, "coluna": "quartil_esc", "rotulos": ["Q1", "Q2", "Q3", "Q4"]},
    "Quintis": {"singular": "Quintil", "n": 5, "coluna": "quintil_esc", "rotulos": ["1º", "2º", "3º", "4º", "5º"]},
}
AGRUPAMENTO_PADRAO = "Tercis"

# Classes de resíduo das perguntas 1 e 4: o critério de ±1 desvio-padrão da
# seção 6.4.1 da Atividade 01, aplicado também à pergunta 1 para que os dois
# mapas se leiam do mesmo jeito.
CLASSES_P1 = [
    "Muito abaixo do esperado (< −1 dp)",
    "Abaixo do esperado",
    "Acima do esperado",
    "Muito acima do esperado (> +1 dp)",
]
CLASSES_P4 = [
    "Produz muito, renda baixa (< −1 dp)",
    "Abaixo do esperado",
    "Acima do esperado",
    "Ganha muito mais do que produz (> +1 dp)",
]

# Pergunta 2, "Quem foge do padrão?": para cada faixa (ou para a base da renda),
# a fatia esperada pela escolaridade e a diferença de cada município. As colunas
# de cada opção são somadas: a base é "sem rendimento" + "mais de 0 até 1 SM".
ALVOS_P2 = {
    "Base da renda (sem rendimento + até 1 SM)": ["pct_sem_rendimento_2010", "pct_ate_1sm_2010"],
    "Sem rendimento": ["pct_sem_rendimento_2010"],
    "Mais de 0 até 1 SM": ["pct_ate_1sm_2010"],
    "Mais de 1 até 2 SM": ["pct_1a2sm_2010"],
    "Mais de 2 até 3 SM": ["pct_2a3sm_2010"],
    "Mais de 3 até 5 SM": ["pct_3a5sm_2010"],
    "Mais de 5 SM": ["pct_mais_5sm_2010"],
}
ALVO_P2_PADRAO = "Base da renda (sem rendimento + até 1 SM)"
CLASSES_P2 = [
    "Muito abaixo do esperado (< −1 dp)",
    "Abaixo do esperado",
    "Acima do esperado",
    "Muito acima do esperado (> +1 dp)",
]

# Paletas das figuras da Atividade 01, para manter a continuidade visual.
# ---------------------------------------------------------------
# Paleta dos mapas
# ---------------------------------------------------------------
# Uma cor base por pergunta. As quatro nunca aparecem juntas — cada pergunta é
# uma página — mas foram escolhidas como conjunto e verificadas par a par, em
# visão normal e sob simulação de protanopia e deuteranopia, para que trocar de
# pergunta seja uma mudança perceptível e não uma variação de tom.
#
# Só os MAPAS seguem estas cores. Os gráficos da Atividade 01 continuam com as
# cores originais do notebook, de propósito: eles existem para corresponder ao
# trabalho anterior, e mudá-los quebraria essa correspondência.
CORES_BASE = {
    "P1": "#2a78d6",   # azul
    "P2": "#eb6834",   # laranja
    "P3": "#1baf7a",   # aqua
    "P4": "#4a3aa7",   # violeta
}

# Toda escala de mapa é uma RAMPA SEQUENCIAL de um tom só, do claro ao escuro,
# no matiz da pergunta. Matizes diferentes anunciariam categorias sem ordem;
# aqui quem diz "mais" e "menos" é a luminosidade, que sobrevive à impressão em
# cinza e a qualquer daltonismo.
#
# O passo mais claro fica em 2:1 contra o fundo do mapa: abaixo disso a classe
# some na superfície e passa a se confundir com o cinza de "sem dado".
CORES_RESIDUO = {
    "P1": ["#8db5eb", "#5c8fd1", "#2a69b7", "#00458e"],   # abaixo → acima
    "P4": ["#acadee", "#8684d3", "#625bb8", "#422f9c"],   # abaixo → acima
}
# P2: a rampa laranja original, de 4 passos (quartis), é a referência. As de 3 e 5
# passos são amostras dessa mesma rampa, com as mesmas pontas (#eba186 e #7c2800).
# Só a de quartis foi verificada para daltonismo; as outras herdam as pontas dela.
CORES_P2 = {
    "Tercis": ["#eba186", "#bd5b34", "#7c2800"],
    "Quartis": ["#eba186", "#cd7352", "#ae4417", "#7c2800"],
    "Quintis": ["#eba186", "#d47e5f", "#bd5b34", "#a13d11", "#7c2800"],
}
# P3, 1º → 5º. A rampa anterior ia de L* 73 a 32 e deixava os vizinhos a ΔE 10–12,
# abaixo do piso de 15: no mapa, com 496 polígonos pequenos, os quintis do meio se
# confundiam. O passo mais claro continua o mesmo (o do contraste 2:1 com o fundo);
# a rampa agora desce até L* 16, com um leve giro para o verde-azulado nos tons
# escuros, e todos os vizinhos ficam a ΔE ≥ 15.
CORES_QUINTIL = ["#82bfa1", "#4f9b79", "#00785d", "#005344", "#00302b"]

# Escala dos gráficos da Atividade 01 — NÃO mexer: é a rampa do notebook.
CORES_FAIXAS = ["#86b6ef", "#5598e7", "#2a78d6", "#256abf", "#184f95", "#0d366b"]
# Mesmas seis faixas, no laranja da página 2, para o gráfico 6.2.1 interativo: o mesmo
# matiz do mapa (pontas #eba186 → #7c2800), estendido para um tom mais claro na base
# (sem rendimento) e um mais escuro no topo (mais de 5 SM). Vizinhos a ΔE ≥ 13,5.
CORES_FAIXAS_P2 = ["#ffd9c9", "#f2ae96", "#d48669", "#b26140", "#913e1a", "#6e1b00"]

# Clareado de #d9d9d9 para cá: contra as rampas novas, o cinza antigo ficava a
# ΔE 14,7 do passo mais claro — abaixo do piso de 15 em que duas cores param de
# ser distinguíveis mesmo com visão de cor completa. Como o tom novo recua para
# perto da superfície, o município sem dado ganha um traço escuro no mapa.
COR_SEM_DADO = "#e4e3e0"
COR_FORA = "#ecebe6"
COR_DESTAQUE = "#eb6834"


@dataclass(frozen=True)
class Modelos:
    """Parâmetros calculados sobre os 496 municípios, fixos para qualquer filtro."""

    n: int
    p1_intercepto: float
    p1_inclinacao: float
    p1_r: float
    p1_dp: float
    p2_limites: dict  # {"Tercis": (cortes...), "Quartis": ..., "Quintis": ...}
    p3_limites: tuple
    p3_mediana_rf1: float
    p4_intercepto: float
    p4_inclinacao: float
    p4_r2: float
    p4_dp: float
    p4_corte_tercil: float
    centro_poa: tuple  # (latitude, longitude)


def carregar():
    """Lê as duas camadas exportadas pelo notebook regioes_funcionais_rs."""
    if not ARQUIVO_MUNICIPIOS.exists() or not ARQUIVO_REGIOES.exists():
        raise FileNotFoundError(
            f"Dados não encontrados em {PASTA_DADOS}. Rode o notebook "
            "regioes_funcionais_rs.ipynb até a seção 9, que grava as cópias nesta pasta.")
    municipios = gpd.read_file(ARQUIVO_MUNICIPIOS)
    municipios["CD_MUN"] = municipios["CD_MUN"].astype(str)
    regioes = gpd.read_file(ARQUIVO_REGIOES)
    return municipios, regioes


def _classificar(residuo, dp, rotulos):
    return pd.cut(residuo, [-np.inf, -dp, 0, dp, np.inf], labels=rotulos)


def calcular(municipios):
    """Acrescenta as colunas das 4 perguntas e devolve os parâmetros fixos."""
    mun = municipios.copy()
    com = mun[RENDA].notna() & mun[ESCOLARIDADE].notna() & mun[PIB].notna()
    base = mun[com]

    # Pergunta 1 — reta escolaridade → renda (mínimos quadrados, como linregress)
    inclinacao, intercepto = np.polyfit(base[ESCOLARIDADE], base[RENDA], 1)
    r_p1 = float(np.corrcoef(base[ESCOLARIDADE], base[RENDA])[0, 1])
    mun["esperado_p1"] = intercepto + inclinacao * mun[ESCOLARIDADE]
    mun["residuo_p1"] = mun[RENDA] - mun["esperado_p1"]
    dp_p1 = float(mun.loc[com, "residuo_p1"].std())
    mun["classe_p1"] = _classificar(mun["residuo_p1"], dp_p1, CLASSES_P1)

    # Pergunta 2 — tercis, quartis e quintis de escolaridade (pd.qcut), todos de uma vez
    limites_p2 = {}
    for nome, ag in AGRUPAMENTOS.items():
        grupo, limites = pd.qcut(base[ESCOLARIDADE], ag["n"], labels=ag["rotulos"], retbins=True)
        mun[ag["coluna"]] = grupo.reindex(mun.index)
        limites_p2[nome] = tuple(float(v) for v in limites)

    # Pergunta 3 — quintis de renda (mapa 6.3.3)
    quintil, limites_p3 = pd.qcut(base[RENDA], 5, labels=False, retbins=True)
    mun["quintil_renda"] = quintil.reindex(mun.index)
    mediana_rf1 = float(base.loc[base["regiao_funcional_id"] == 1, RENDA].median())

    # Pergunta 4 — renda esperada pelo log do PIB per capita (seção 6.4.1)
    log_pib = np.log10(base[PIB] / 1000)
    inclinacao_p4, intercepto_p4 = np.polyfit(log_pib, base[RENDA], 1)
    mun["esperado_p4"] = intercepto_p4 + inclinacao_p4 * np.log10(mun[PIB] / 1000)
    mun["residuo_p4"] = mun[RENDA] - mun["esperado_p4"]
    dp_p4 = float(mun.loc[com, "residuo_p4"].std())
    r2_p4 = float(np.corrcoef(mun.loc[com, "esperado_p4"], base[RENDA])[0, 1]) ** 2
    mun["classe_p4"] = _classificar(mun["residuo_p4"], dp_p4, CLASSES_P4)
    corte = float(base[PIB].quantile(1 / 3))
    mun["tercil_inferior_pib"] = com & (mun[PIB] <= corte)
    mun["destaque_p4"] = mun["tercil_inferior_pib"] & (mun["residuo_p4"] > dp_p4)

    # Setor com maior participação e quanto ele representa
    participacoes = mun[list(SETORES)]
    mun["pct_setor_lider"] = participacoes.max(axis=1)

    poa = mun.loc[mun["NM_MUN"] == "Porto Alegre"].to_crs(mun.estimate_utm_crs())
    centro = gpd.GeoSeries([poa.geometry.iloc[0].centroid], crs=poa.crs).to_crs(4326).iloc[0]

    modelos = Modelos(
        n=int(com.sum()),
        p1_intercepto=float(intercepto), p1_inclinacao=float(inclinacao),
        p1_r=r_p1, p1_dp=dp_p1,
        p2_limites=limites_p2,
        p3_limites=tuple(float(v) for v in limites_p3),
        p3_mediana_rf1=mediana_rf1,
        p4_intercepto=float(intercepto_p4), p4_inclinacao=float(inclinacao_p4),
        p4_r2=r2_p4, p4_dp=dp_p4, p4_corte_tercil=corte,
        centro_poa=(centro.y, centro.x),
    )
    return mun, modelos


def formatar(valor, casas=0, prefixo="", sufixo="", sinal=False):
    """Número no padrão brasileiro; `sem dado` para ausentes."""
    if valor is None or pd.isna(valor):
        return "sem dado"
    padrao = f"{{:{'+' if sinal else ''},.{casas}f}}"
    numero = padrao.format(valor).replace(",", "\x00").replace(".", ",").replace("\x00", ".")
    if sinal and numero[:1] in "+-":   # sinal antes do prefixo: "+R$ 61", não "R$ +61"
        return f"{'−' if numero[0] == '-' else '+'}{prefixo}{numero[1:]}{sufixo}"
    return f"{prefixo}{numero}{sufixo}"


def reais(valor, casas=0, sinal=False):
    return formatar(valor, casas, prefixo="R$ ", sinal=sinal)


def medias_faixas(municipios, agrupamento=AGRUPAMENTO_PADRAO):
    """Média das distribuições municipais por grupo de escolaridade (seção 6.2).

    `agrupamento` é "Tercis", "Quartis" ou "Quintis" (chaves de AGRUPAMENTOS).
    """
    coluna = AGRUPAMENTOS[agrupamento]["coluna"]
    com = municipios.dropna(subset=[coluna])
    medias = com.groupby(coluna, observed=False)[list(FAIXAS)].mean()
    contagem = com.groupby(coluna, observed=False).size()
    return medias.rename(columns=FAIXAS), contagem


def _logit(p):
    p = np.clip(p, 0.005, 0.995)
    return np.log(p / (1 - p))


def curva_p2(coef, escolaridade):
    """Fatia esperada (%) para um % de ocupados com ensino médio, dada a curva ajustada."""
    inclinacao, intercepto = coef
    return 100 / (1 + np.exp(-(intercepto + inclinacao * np.asarray(escolaridade, float))))


def afastamento_p2(municipios, alvo=ALVO_P2_PADRAO):
    """Fatia observada × esperada pela escolaridade, para a faixa `alvo` (chave de ALVOS_P2).

    A curva é ajustada UMA vez, sobre os 496 municípios com dado, como as retas
    das perguntas 1 e 4; o filtro do dashboard só escolhe o que aparece.

    Por que curva e não reta: a fatia é uma porcentagem, e uma reta ultrapassa
    os limites — na base da renda ela chega a −8,7% em Porto Alegre, que então
    aparece como falso destaque. O ajuste é linear no logito da fatia
    (log(p / (1 − p))), e a volta para % mantém a curva entre 0 e 100.

    Devolve (DataFrame alinhado a `municipios` com observado, esperado,
    diferenca e classe; coeficientes da curva; desvio-padrão da diferença).
    """
    com = municipios[RENDA].notna() & municipios[ESCOLARIDADE].notna()
    observado = municipios[ALVOS_P2[alvo]].sum(axis=1, min_count=1)
    base = municipios[com]
    coef = np.polyfit(base[ESCOLARIDADE], _logit(observado[com] / 100), 1)
    esperado = pd.Series(curva_p2(coef, municipios[ESCOLARIDADE]), index=municipios.index)
    diferenca = (observado - esperado).where(com)
    dp = float(diferenca[com].std())
    resultado = pd.DataFrame({
        "observado": observado, "esperado": esperado, "diferenca": diferenca,
        "classe": _classificar(diferenca, dp, CLASSES_P2),
    })
    return resultado, tuple(float(c) for c in coef), dp


DISCRIMINANTES_P4 = {
    ESCOLARIDADE: "Ocupados com ensino médio completo (%)",
    POPULACAO: "População (habitantes, Censo 2010)",
    "pct_vab_servicos_2010": "Serviços no valor adicionado (%)",
    "pct_vab_agropecuaria_2010": "Agropecuária no valor adicionado (%)",
    "pct_vab_industria_2010": "Indústria no valor adicionado (%)",
    "pct_vab_adm_publica_2010": "Administração pública no valor adicionado (%)",
}


def testes_p4(municipios, n_permutacoes=20000, semente=7):
    """p-valor da diferença de medianas entre os dois grupos do tercil inferior de PIB.

    Mesmo teste da seção 6.4.1: embaralha os rótulos dos grupos e mede quão
    extrema é a diferença observada. As permutações são geradas de uma vez, em
    matriz, então os p-valores podem diferir na terceira casa dos publicados.
    """
    baixo = municipios[municipios["tercil_inferior_pib"]]
    alto = baixo["destaque_p4"].to_numpy()
    rng = np.random.default_rng(semente)
    ordens = np.argsort(rng.random((n_permutacoes, len(baixo))), axis=1)
    p = {}
    for coluna in DISCRIMINANTES_P4:
        valores = baixo[coluna].to_numpy(float)
        observada = np.median(valores[alto]) - np.median(valores[~alto])
        embaralhados = valores[ordens]
        k = int(alto.sum())
        difs = np.median(embaralhados[:, :k], axis=1) - np.median(embaralhados[:, k:], axis=1)
        p[coluna] = float((np.abs(difs) >= abs(observada)).mean())
    return p


def _conferir():
    municipios, regioes = carregar()
    mun, m = calcular(municipios)
    assert len(mun) == 497 and len(regioes) == 9
    assert m.n == 496

    def perto(obtido, esperado, tolerancia, nome, referencia="Atividade 01"):
        ok = abs(obtido - esperado) <= tolerancia
        print(f"  [{'ok' if ok else 'DIFERE'}] {nome}: {obtido:,.2f} ({referencia}: {esperado})")
        assert ok, nome

    print("Pergunta 1")
    perto(m.p1_r, 0.70, 0.005, "r de Pearson escolaridade × renda")

    print("Pergunta 2 — quartis (notebook da Atividade 01)")
    lq = m.p2_limites["Quartis"]
    perto(lq[1], 22.7, 0.05, "limite Q1/Q2 (%)")
    perto(lq[3], 35.7, 0.05, "limite Q3/Q4 (%)")
    medias, contagem = medias_faixas(mun, "Quartis")
    perto(medias.loc["Q1", "Sem rendimento"], 18.2, 0.05, "Q1 sem rendimento (%)")
    perto(medias.loc["Q4", "Sem rendimento"], 4.8, 0.05, "Q4 sem rendimento (%)")
    perto(medias.loc["Q1", "Mais de 0 até 1 SM"], 28.5, 0.05, "Q1 até 1 SM (%)")
    perto(medias.loc["Q4", "Mais de 5 SM"], 7.6, 0.05, "Q4 mais de 5 SM (%)")

    print("Pergunta 2 — tercis (Atividade 02, grafico2_altair.py)")
    lt = m.p2_limites["Tercis"]
    perto(lt[1], 24.6, 0.05, "limite T1/T2 (%)", "Atividade 02")
    perto(lt[2], 33.0, 0.05, "limite T2/T3 (%)", "Atividade 02")
    medias, contagem = medias_faixas(mun, "Tercis")
    perto(contagem["T1"], 167, 0, "municípios no T1", "Atividade 02")
    perto(contagem["T3"], 165, 0, "municípios no T3", "Atividade 02")
    perto(medias.loc["T1", "Sem rendimento"], 17.7, 0.05, "T1 sem rendimento (%)", "Atividade 02")
    perto(medias.loc["T3", "Sem rendimento"], 5.8, 0.05, "T3 sem rendimento (%)", "Atividade 02")

    print("Pergunta 2 — quintis (consistência)")
    medias, contagem = medias_faixas(mun, "Quintis")
    perto(contagem.sum(), 496, 0, "municípios nos 5 quintis", "esperado")
    perto(float(contagem.max() - contagem.min() <= 2), 1, 0,
          "quintis com tamanhos parecidos (diferença de até 2 municípios)", "esperado")
    queda = medias["Sem rendimento"].diff().dropna()
    perto(float((queda < 0).all()), 1, 0, "'sem rendimento' cai a cada quintil", "esperado")

    print("Pergunta 2 — quem foge do padrão (Atividade 02)")
    af, _, dp_af = afastamento_p2(mun)
    af["nome"] = mun["NM_MUN"]
    ordem = af.dropna(subset=["diferenca"]).sort_values("diferenca")
    perto(float(ordem["nome"].iloc[-1] == "Dezesseis de Novembro"), 1, 0,
          "maior diferença positiva: Dezesseis de Novembro", "esperado")
    perto(float(ordem["nome"].iloc[0] == "Nova Hartz"), 1, 0,
          "maior diferença negativa: Nova Hartz", "esperado")
    perto(float(af.loc[mun["NM_MUN"] == "Porto Alegre", "esperado"].iloc[0]), 5.1, 0.1,
          "base esperada em Porto Alegre, dentro de 0–100% (%)", "Atividade 02")
    perto(dp_af, 10.3, 0.1, "desvio-padrão da diferença (p.p.)", "Atividade 02")

    print("Pergunta 3")
    medianas = mun.groupby("regiao_funcional")[RENDA].median()
    perto(medianas["RF3 · Serra e Hortênsias"], 1173, 1, "mediana RF3 (R$)")
    perto(m.p3_mediana_rf1, 997, 1, "mediana RF1 (R$)")

    print("Pergunta 4")
    perto(m.p4_dp, 240, 1, "desvio-padrão do resíduo (R$)")
    perto(m.p4_r2, 0.21, 0.01, "R²")
    perto(m.p4_corte_tercil, 13284, 1, "corte do tercil inferior (R$/hab.)")
    perto((mun["residuo_p4"] > m.p4_dp).sum(), 72, 0, "ganham muito mais do que produzem")
    perto((mun["residuo_p4"] < -m.p4_dp).sum(), 75, 0, "produzem muito, renda baixa")
    perto(mun["destaque_p4"].sum(), 13, 0, "tercil inferior com renda acima do esperado")
    perto(mun["tercil_inferior_pib"].sum(), 166, 0, "municípios no tercil inferior")
    p = testes_p4(mun)
    perto(p["pct_vab_adm_publica_2010"], 0.2382, 0.03, "p da administração pública (não distingue)")
    perto(p["pct_vab_industria_2010"], 0.0040, 0.005, "p da indústria")
    for coluna in (ESCOLARIDADE, POPULACAO, "pct_vab_servicos_2010", "pct_vab_agropecuaria_2010"):
        perto(p[coluna], 0.0, 0.0001, f"p {DISCRIMINANTES_P4[coluna]}")
    print("\nTodos os valores conferem com as Atividades 01 e 02.")


if __name__ == "__main__":
    _conferir()
