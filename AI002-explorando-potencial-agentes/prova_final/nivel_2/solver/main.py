"""Ponto de entrada: python -m solver [opções]."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
from dataclasses import asdict, fields
from pathlib import Path

from .abordagens import ResultadoTarefa, resolver_codigo, resolver_fim_a_fim

log = logging.getLogger("solver")

ABORDAGENS = ("fim_a_fim", "codigo")
COLUNAS = [f.name for f in fields(ResultadoTarefa)]


def carregar_tarefas(lista: Path) -> list[tuple[str, str, dict]]:
    """Lê tarefas.txt e devolve (id, conjunto, conteúdo) para cada linha."""
    base = lista.parent
    tarefas = []
    for linha in lista.read_text(encoding="utf-8").splitlines():
        caminho = linha.strip()
        if not caminho:
            continue
        arquivo = base / caminho  # ex.: training/3aa6fb7a.json
        tarefas.append((arquivo.stem, arquivo.parent.name, json.loads(arquivo.read_text(encoding="utf-8"))))
    return tarefas


def ler_resultados(arquivo: Path) -> dict[str, dict]:
    """Linhas já gravadas, indexadas pelo id da tarefa. Permite retomar a execução."""
    if not arquivo.exists():
        return {}
    with arquivo.open(encoding="utf-8", newline="") as f:
        return {linha["tarefa"]: linha for linha in csv.DictReader(f)}


class ConfiguracaoMisturada(Exception):
    """Os resultados gravados vieram de outro modelo ou nível de raciocínio."""


def verificar_configuracao(feitas: dict[str, dict], modelo, arquivo: Path) -> None:
    """Impede misturar, no mesmo arquivo, linhas de modelos ou níveis de raciocínio diferentes.

    Sem isso, retomar uma execução com outro --raciocinio produziria totais que
    somam duas configurações, sem nenhum aviso.
    """
    atual = (modelo.modelo, modelo.raciocinio)
    for tarefa, linha in feitas.items():
        gravada = (linha.get("modelo"), linha.get("raciocinio"))
        if gravada != atual:
            raise ConfiguracaoMisturada(
                f"{arquivo.name}: a tarefa {tarefa} foi gravada com modelo={gravada[0]} e "
                f"raciocinio={gravada[1]}, mas esta execução usa modelo={atual[0]} e "
                f"raciocinio={atual[1]}. Use outra pasta com --saida ou apague o arquivo."
            )


def anexar_resultado(arquivo: Path, resultado: ResultadoTarefa) -> None:
    """Grava uma linha logo que a tarefa termina, para não perder trabalho numa queda."""
    novo = not arquivo.exists()
    with arquivo.open("a", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=COLUNAS)
        if novo:
            escritor.writeheader()
        linha = asdict(resultado)
        linha["segundos"] = round(linha["segundos"], 2)
        escritor.writerow(linha)


def resumir(linhas: list[dict], abordagem: str) -> dict:
    """Totais de uma abordagem, calculados a partir do CSV."""
    def soma(campo: str) -> float:
        return sum(float(l[campo]) for l in linhas)

    resumo = {
        "abordagem": abordagem,
        # Se houver mais de um valor, aparecem todos, e a mistura fica visível.
        "modelo": ", ".join(sorted({l["modelo"] for l in linhas})),
        "raciocinio": ", ".join(sorted({l["raciocinio"] for l in linhas})),
        "tarefas": len(linhas),
        "resolvidas": sum(l["resolvida"] == "True" for l in linhas),
        "resolvidas_treino": sum(l["resolvida"] == "True" and l["conjunto"] == "training" for l in linhas),
        "resolvidas_avaliacao": sum(l["resolvida"] == "True" and l["conjunto"] == "evaluation" for l in linhas),
        "tokens_entrada": int(soma("tokens_entrada")),
        "tokens_raciocinio": int(soma("tokens_raciocinio")),
        "tokens_saida": int(soma("tokens_saida")),
        "segundos": round(soma("segundos"), 1),
    }
    if abordagem == "codigo":
        resumo["treino_ok"] = sum(l["treino_ok"] == "True" for l in linhas)
        resumo["treino_ok_e_teste_errado"] = sum(
            l["treino_ok"] == "True" and l["resolvida"] == "False" for l in linhas
        )
    return resumo


def escrever_resumo(saida: Path) -> list[dict]:
    """Gera resumo.json e resumo.md com uma linha por abordagem."""
    resumos = []
    for abordagem in ABORDAGENS:
        linhas = list(ler_resultados(saida / f"{abordagem}.csv").values())
        if linhas:
            resumos.append(resumir(linhas, abordagem))
    (saida / "resumo.json").write_text(json.dumps(resumos, indent=2, ensure_ascii=False), encoding="utf-8")

    md = ["| Abordagem | Modelo | Nível de raciocínio | Resolvidas | Treino ok | Entrada | Raciocínio | Saída | Tempo (s) |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in resumos:
        treino = str(r["treino_ok"]) if "treino_ok" in r else "-"
        md.append(f"| {r['abordagem']} | {r['modelo']} | {r['raciocinio']} | {r['resolvidas']}/{r['tarefas']} | {treino} | {r['tokens_entrada']} | "
                  f"{r['tokens_raciocinio']} | {r['tokens_saida']} | {r['segundos']} |")
    (saida / "resumo.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    return resumos


def executar_experimento(modelo, tarefas, abordagens, saida: Path, limite_execucao: float) -> int:
    """Roda as abordagens e devolve quantas chamadas falharam de vez."""
    falhas = 0
    for abordagem in abordagens:
        arquivo = saida / f"{abordagem}.csv"
        feitas = ler_resultados(arquivo)
        verificar_configuracao(feitas, modelo, arquivo)
        pasta_respostas = saida / "respostas" / abordagem
        pasta_respostas.mkdir(parents=True, exist_ok=True)
        log.info("=== %s: %d tarefas, %d já feitas ===", abordagem, len(tarefas), len(feitas))

        for tarefa_id, conjunto, tarefa in tarefas:
            if tarefa_id in feitas:
                continue
            try:
                if abordagem == "fim_a_fim":
                    resultado, bruto = resolver_fim_a_fim(modelo, tarefa_id, conjunto, tarefa)
                    extensao = ".txt"
                else:
                    resultado, bruto = resolver_codigo(modelo, tarefa_id, conjunto, tarefa, limite_execucao)
                    extensao = ".py"
            except Exception as erro:
                # Falha da API mesmo após as retentativas. Não gravamos a linha:
                # assim, rodar de novo tenta esta tarefa outra vez.
                falhas += 1
                log.error("%s: falha na chamada (%s: %s)", tarefa_id, type(erro).__name__, erro)
                continue

            # Guardar a resposta bruta permite analisar acertos e erros no relatório.
            (pasta_respostas / f"{tarefa_id}{extensao}").write_text(bruto, encoding="utf-8")
            anexar_resultado(arquivo, resultado)
            situacao = "RESOLVIDA" if resultado.resolvida else "não resolvida"
            treino = "" if resultado.treino_ok is None else f" treino_ok={resultado.treino_ok}"
            log.info("%s: %s%s (entrada %d, raciocínio %d, saída %d, %.1f s) %s",
                     tarefa_id, situacao, treino, resultado.tokens_entrada, resultado.tokens_raciocinio,
                     resultado.tokens_saida, resultado.segundos, resultado.erro)
    return falhas


def main(argv: list[str] | None = None) -> int:
    raiz = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description="Resolve tarefas do ARC-AGI-1 com o Gemini.")
    parser.add_argument("--tarefas", type=Path, default=raiz / "tarefas" / "tarefas.txt")
    parser.add_argument("--saida", type=Path, default=raiz / "resultados")
    parser.add_argument("--abordagens", nargs="+", choices=ABORDAGENS, default=list(ABORDAGENS))
    parser.add_argument("--modelo", default="gemini-3.5-flash-lite")
    parser.add_argument("--raciocinio", default="high", help="nível de raciocínio do Gemini")
    parser.add_argument("--limite-execucao", type=float, default=10.0,
                        help="tempo limite, em segundos, para rodar o código gerado")
    parser.add_argument("--teste-rapido", action="store_true",
                        help="roda só 2 tarefas, uma de cada conjunto, em resultados_teste/")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")

    tarefas = carregar_tarefas(args.tarefas)
    if args.teste_rapido:
        tarefas = [next(t for t in tarefas if t[1] == c) for c in ("training", "evaluation")]
        if args.saida == raiz / "resultados":
            args.saida = raiz / "resultados_teste"  # não mistura com o experimento real
    args.saida.mkdir(parents=True, exist_ok=True)

    # Importados aqui para que os testes não dependam da biblioteca nem da chave.
    from dotenv import load_dotenv
    from .llm import ClienteGemini

    load_dotenv(raiz / ".env")
    chave = os.environ.get("GOOGLE_API_KEY", "").strip()
    if not chave:
        log.error("GOOGLE_API_KEY não encontrada. Copie .env.example para .env e preencha a chave.")
        return 2

    modelo = ClienteGemini(chave, modelo=args.modelo, raciocinio=args.raciocinio)
    try:
        falhas = executar_experimento(modelo, tarefas, args.abordagens, args.saida, args.limite_execucao)
    except ConfiguracaoMisturada as erro:
        log.error("%s", erro)
        return 2
    for r in escrever_resumo(args.saida):
        log.info("Resumo: %s", r)
    if falhas:
        log.warning("%d chamadas falharam. Rode o mesmo comando de novo para completar.", falhas)
        return 1
    return 0
