"""Gera as figuras do relatório a partir dos JSON das tarefas.

Rodar a partir da raiz do projeto:  .venv/bin/python figuras/gerar_figuras.py
Requer matplotlib, que só é usado aqui e não pelo solver.
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # sem janela: só grava arquivos
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

RAIZ = Path(__file__).resolve().parent.parent

# Paleta padrão do ARC: o número de 0 a 9 de cada célula é uma cor fixa.
# É a mesma paleta do notebook do nível 1.
CORES = ListedColormap([
    "#000000", "#0074D9", "#FF4136", "#2ECC40", "#FFDC00",
    "#AAAAAA", "#F012BE", "#FF851B", "#7FDBFF", "#870C25",
])

plt.rcParams.update({"font.family": "serif", "font.size": 7, "pdf.fonttype": 42})


def carregar(conjunto: str, tarefa: str) -> dict:
    return json.loads((RAIZ / "tarefas" / conjunto / f"{tarefa}.json").read_text())


def desenhar(eixo, grade, titulo):
    altura, largura = len(grade), len(grade[0])
    eixo.imshow(grade, cmap=CORES, vmin=0, vmax=9, interpolation="nearest")
    # Linhas finas entre as células, para contar posições e ver o fundo preto.
    eixo.set_xticks([x - 0.5 for x in range(1, largura)], minor=True)
    eixo.set_yticks([y - 0.5 for y in range(1, altura)], minor=True)
    eixo.grid(which="minor", color="#444444", linewidth=0.3)
    eixo.tick_params(which="both", length=0, labelbottom=False, labelleft=False)
    for borda in eixo.spines.values():
        borda.set_color("#888888")
        borda.set_linewidth(0.6)
    eixo.set_title(titulo, fontsize=7, pad=2)


def figura(conjunto, tarefa, n_treino, arquivo):
    """Primeira linha: entradas. Segunda linha: saídas. Última coluna: o teste."""
    dados = carregar(conjunto, tarefa)
    pares = dados["train"][:n_treino]
    teste = dados["test"][0]
    colunas = n_treino + 1
    fig, eixos = plt.subplots(2, colunas, figsize=(3.3, 2.15))
    for i, par in enumerate(pares):
        desenhar(eixos[0][i], par["input"], f"Treino {i + 1}: entrada")
        desenhar(eixos[1][i], par["output"], f"Treino {i + 1}: saída")
    desenhar(eixos[0][-1], teste["input"], "Teste: entrada")
    desenhar(eixos[1][-1], teste["output"], "Teste: resposta")
    fig.subplots_adjust(left=0.01, right=0.99, top=0.93, bottom=0.01, wspace=0.12, hspace=0.22)
    fig.savefig(RAIZ / "figuras" / arquivo)
    plt.close(fig)


if __name__ == "__main__":
    figura("training", "3aa6fb7a", 2, "arc_3aa6fb7a.pdf")
    figura("training", "44d8ac46", 2, "arc_44d8ac46.pdf")
    print("Figuras gravadas em figuras/.")
