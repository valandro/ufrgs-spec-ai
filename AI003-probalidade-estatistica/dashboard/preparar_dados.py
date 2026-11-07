"""Gera dados/populacao.csv e dados/amostra.csv a partir dos boletins de urna do TSE.

Executar uma vez (lê ~1,6 GB de CSV); o dashboard usa apenas os arquivos gerados.
Mesma lógica e semente do notebook trabalho_final_organizacao.ipynb.
"""
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
CSV_1T = RAIZ / "bweb_1t_RS_051020261403" / "bweb_1t_RS_051020261403.csv"
CSV_2T = RAIZ / "bweb_2t_RS_261020260742" / "bweb_2t_RS_261020260742.csv"
SAIDA = Path(__file__).resolve().parent / "dados"

MUNICIPIO, CARGO = "PORTO ALEGRE", "Presidente"
CHAVE = ["NR_ZONA", "NR_SECAO"]
COLS = ["NM_MUNICIPIO", "NR_ZONA", "NR_SECAO", "DS_CARGO_PERGUNTA", "QT_APTOS", "QT_COMPARECIMENTO",
        "QT_ABSTENCOES", "DS_TIPO_VOTAVEL", "NM_VOTAVEL", "QT_VOTOS"]
SEED, N_AMOSTRA = 42, 793   # n de tamanho_amostra(N=3077, conf=0.95, erro=0.03, p=0.5)


def agrega_turno(caminho, sufixo):
    pedacos = []
    for ch in pd.read_csv(caminho, sep=";", encoding="latin1", usecols=COLS, chunksize=500_000):
        pedacos.append(ch[(ch.NM_MUNICIPIO == MUNICIPIO) & (ch.DS_CARGO_PERGUNTA == CARGO)])
    d = pd.concat(pedacos)
    base = d[CHAVE + ["QT_APTOS", "QT_COMPARECIMENTO", "QT_ABSTENCOES"]].drop_duplicates(CHAVE).set_index(CHAVE)
    votos = d[d.DS_TIPO_VOTAVEL == "Nominal"].pivot_table(
        index=CHAVE, columns="NM_VOTAVEL", values="QT_VOTOS", aggfunc="sum", fill_value=0)
    out = base.join(votos[["LULA", "FLAVIO BOLSONARO"]])
    out["VOTOS_VALIDOS"] = votos.sum(axis=1)
    out["QT_BRANCO_NULO"] = d[d.DS_TIPO_VOTAVEL.isin(["Branco", "Nulo"])].groupby(CHAVE).QT_VOTOS.sum()
    out["QT_BRANCO_NULO"] = out.QT_BRANCO_NULO.fillna(0)
    total = out.VOTOS_VALIDOS + out.QT_BRANCO_NULO                 # votos totais = válidos + brancos + nulos
    out["VENCEDOR"] = np.where(out.LULA > out["FLAVIO BOLSONARO"], "LULA", "FLAVIO BOLSONARO")
    out["PCT_LULA"] = out.LULA / out.VOTOS_VALIDOS * 100
    out["PCT_FLAVIO"] = out["FLAVIO BOLSONARO"] / out.VOTOS_VALIDOS * 100
    out["PCT_LULA_TOTAL"] = out.LULA / total * 100                    # % sobre votos totais (inclui brancos e nulos)
    out["PCT_FLAVIO_TOTAL"] = out["FLAVIO BOLSONARO"] / total * 100
    out["PCT_BRANCO_NULO"] = out.QT_BRANCO_NULO / total * 100
    out["PCT_ABSTENCAO"] = out.QT_ABSTENCOES / out.QT_APTOS * 100
    return out.add_suffix("_" + sufixo)


def main():
    pop = agrega_turno(CSV_1T, "1t").join(agrega_turno(CSV_2T, "2t"), how="inner").reset_index()
    pop["DELTA_LULA_PP"] = pop.PCT_LULA_2t - pop.PCT_LULA_1t
    pop["DELTA_LULA_TOTAL_PP"] = pop.PCT_LULA_TOTAL_2t - pop.PCT_LULA_TOTAL_1t
    pop["DELTA_ABST_PP"] = pop.PCT_ABSTENCAO_2t - pop.PCT_ABSTENCAO_1t
    pop["MUDOU_VENCEDOR"] = np.where(pop.VENCEDOR_1t != pop.VENCEDOR_2t, "Sim", "Não")
    pop["TRAJETORIA"] = pop.VENCEDOR_1t.str.split().str[0] + " → " + pop.VENCEDOR_2t.str.split().str[0]

    amostra = pop.sample(n=N_AMOSTRA, replace=False, random_state=SEED)
    SAIDA.mkdir(exist_ok=True)
    pop.to_csv(SAIDA / "populacao.csv", index=False)
    amostra.to_csv(SAIDA / "amostra.csv", index=False)
    print(f"população: {len(pop)} seções | amostra: {len(amostra)} seções")


if __name__ == "__main__":
    main()
