#!/usr/bin/env python3
"""
Coleta uma série temporal do SGS/BCB (BCData) e grava um CSV.

Série padrão: 29038 - Endividamento das famílias com o Sistema Financeiro
Nacional, exceto crédito habitacional, em relação à renda acumulada dos
últimos 12 meses (% ao ano). A série é mensal.

Sem dependências externas: usa apenas a biblioteca padrão do Python 3.8+.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import datetime

API_BASE = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"
DATE_FMT = "%d/%m/%Y"
TIMEOUT = 30  # segundos


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def parse_cli(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Baixa uma série do SGS/BCB e gera um CSV. "
            "Padrão: série 29038 (endividamento das famílias, exceto habitacional)."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "-i", "--inicio", metavar="dd/MM/aaaa", default=None,
        help="Data inicial da consulta. Se omitida, pega desde o começo da série.",
    )
    parser.add_argument(
        "-f", "--fim", metavar="dd/MM/aaaa", default=None,
        help="Data final da consulta. Se omitida, pega até o dado mais recente.",
    )
    parser.add_argument(
        "-s", "--serie", type=int, default=29038,
        help="Código da série no SGS.",
    )
    parser.add_argument(
        "-o", "--saida", default="endividamento_familias.csv",
        help="Caminho do arquivo CSV de saída.",
    )
    parser.add_argument(
        "-g", "--agrupar", choices=["mes", "ano"], default="ano",
        help="Nível de agrupamento: 'mes' (dado bruto) ou 'ano' (agregado anual).",
    )
    parser.add_argument(
        "--excel-br", action="store_true",
        help="Gera CSV amigável ao Excel PT-BR (delimitador ';' e vírgula decimal).",
    )
    return parser.parse_args(argv)


# --------------------------------------------------------------------------- #
# Validação e URL
# --------------------------------------------------------------------------- #
def validar_data(texto: str | None, rotulo: str) -> str | None:
    """Valida o formato dd/MM/aaaa. Retorna a própria string ou encerra o script."""
    if texto is None:
        return None
    try:
        datetime.strptime(texto, DATE_FMT)
    except ValueError:
        sys.exit(f"[erro] {rotulo} inválida: '{texto}'. Use o formato dd/MM/aaaa.")
    return texto


def montar_url(serie: int, inicio: str | None, fim: str | None) -> str:
    params: dict[str, str] = {"formato": "json"}
    if inicio:
        params["dataInicial"] = inicio
    if fim:
        params["dataFinal"] = fim
    query = urllib.parse.urlencode(params)
    return f"{API_BASE}.{serie}/dados?{query}"


# --------------------------------------------------------------------------- #
# Download
# --------------------------------------------------------------------------- #
def baixar_serie(url: str) -> list[dict]:
    req = urllib.request.Request(url, headers={"User-Agent": "sgs-bcb-client/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            bruto = resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        sys.exit(f"[erro] HTTP {e.code} ao consultar a API do BCB: {e.reason}")
    except urllib.error.URLError as e:
        sys.exit(f"[erro] Falha de conexão com a API do BCB: {e.reason}")

    try:
        dados = json.loads(bruto)
    except json.JSONDecodeError:
        sys.exit("[erro] Resposta da API não é um JSON válido (série ou período inexistente?).")

    if not dados:
        sys.exit("[aviso] A API retornou uma lista vazia para os parâmetros informados.")
    return dados


# --------------------------------------------------------------------------- #
# Transformação
# --------------------------------------------------------------------------- #
def normalizar(registros: list[dict]) -> list[dict]:
    """Converte 'valor' (string) em float e a data em objeto date; ordena por data."""
    saida = []
    for r in registros:
        valor_txt = (r.get("valor") or "").strip()
        if not valor_txt:  # meses sem observação vêm vazios em algumas séries
            continue
        try:
            valor = float(valor_txt)
        except ValueError:
            continue
        data = datetime.strptime(r["data"], DATE_FMT).date()
        saida.append({"data": data, "valor": valor})
    saida.sort(key=lambda x: x["data"])
    return saida


def agrupar_por_ano(registros: list[dict]) -> list[dict]:
    """Agrega a série mensal em estatísticas anuais."""
    baldes: dict[int, list[dict]] = defaultdict(list)
    for r in registros:
        baldes[r["data"].year].append(r)

    linhas = []
    for ano in sorted(baldes):
        itens = sorted(baldes[ano], key=lambda x: x["data"])
        valores = [i["valor"] for i in itens]
        linhas.append({
            "ano": ano,
            "qtd_meses": len(valores),
            "media": round(sum(valores) / len(valores), 4),
            "minimo": round(min(valores), 2),
            "maximo": round(max(valores), 2),
            "ultimo_valor": round(itens[-1]["valor"], 2),
        })
    return linhas


# --------------------------------------------------------------------------- #
# Escrita do CSV
# --------------------------------------------------------------------------- #
def escrever_csv(linhas: list[dict], colunas: list[str], caminho: str, excel_br: bool) -> None:
    delimitador = ";" if excel_br else ","

    def fmt(v):
        if excel_br and isinstance(v, float):
            return str(v).replace(".", ",")
        return v

    with open(caminho, "w", newline="", encoding="utf-8-sig") as fp:
        writer = csv.DictWriter(fp, fieldnames=colunas, delimiter=delimitador)
        writer.writeheader()
        for linha in linhas:
            writer.writerow({c: fmt(linha[c]) for c in colunas})


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> None:
    args = parse_cli(argv)

    inicio = validar_data(args.inicio, "Data inicial")
    fim = validar_data(args.fim, "Data final")
    if inicio and fim and datetime.strptime(inicio, DATE_FMT) > datetime.strptime(fim, DATE_FMT):
        sys.exit("[erro] A data inicial não pode ser posterior à data final.")

    url = montar_url(args.serie, inicio, fim)
    print(f"[info] Consultando: {url}")

    registros = normalizar(baixar_serie(url))
    if not registros:
        sys.exit("[aviso] Nenhuma observação válida após a normalização.")

    if args.agrupar == "ano":
        linhas = agrupar_por_ano(registros)
        colunas = ["ano", "qtd_meses", "media", "minimo", "maximo", "ultimo_valor"]
    else:  # mes
        linhas = [
            {
                "data": r["data"].strftime("%Y-%m-%d"),
                "ano": r["data"].year,
                "mes": r["data"].month,
                "valor": round(r["valor"], 2),
            }
            for r in registros
        ]
        colunas = ["data", "ano", "mes", "valor"]

    escrever_csv(linhas, colunas, args.saida, args.excel_br)
    print(f"[ok] {len(linhas)} linha(s) gravada(s) em '{args.saida}' "
          f"(agrupamento: {args.agrupar}).")


if __name__ == "__main__":
    main()