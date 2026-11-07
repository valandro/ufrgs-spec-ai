"""Executa a função transform(grid) gerada pelo LLM em um processo separado.

Por que um processo separado, e não exec() no próprio solver?
- O código vem do modelo e ninguém o revisou. Ele pode entrar em laço infinito,
  consumir memória ou lançar exceções. Em outro processo, o tempo limite mata
  apenas o filho, e o solver continua com a próxima tarefa.
- O custo é iniciar um interpretador Python por execução, cerca de 50 ms,
  pequeno perto dos segundos de uma chamada ao LLM.

Limitação: isto isola falhas, mas não é uma sandbox de segurança. O processo
filho ainda pode ler arquivos e acessar a rede. Para um experimento acadêmico
isso é aceitável. Em produção, use um contêiner sem rede e com limites de recursos.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from dataclasses import dataclass

Grade = list[list[int]]

# Este trecho é anexado ao código gerado. Ele lê as grades da entrada padrão,
# chama transform() em cada uma e imprime o resultado como JSON na última linha.
# Assim, prints de depuração feitos pelo código gerado não atrapalham a leitura.
_RODAPE = """

import json as _json, sys as _sys

def _normalizar(grade):
    # Aceita listas, tuplas ou arrays NumPy e devolve lista de listas de int.
    if hasattr(grade, "tolist"):
        grade = grade.tolist()
    return [[int(valor) for valor in linha] for linha in grade]

_grades = _json.loads(_sys.stdin.read())
print(_json.dumps([_normalizar(transform(g)) for g in _grades]))
"""


@dataclass(frozen=True)
class ResultadoExecucao:
    """Saídas produzidas, ou None se houve falha, e a mensagem de erro."""

    saidas: list[Grade] | None
    erro: str | None


def executar(codigo: str, grades: list[Grade], limite_segundos: float = 10.0) -> ResultadoExecucao:
    """Aplica transform() a cada grade e devolve as saídas ou o erro."""
    if not grades:
        return ResultadoExecucao(saidas=[], erro=None)

    # Diretório temporário vazio como pasta de trabalho, para o código gerado
    # não escrever arquivos dentro do projeto.
    with tempfile.TemporaryDirectory() as pasta:
        try:
            processo = subprocess.run(
                # -I: modo isolado. Ignora variáveis PYTHON* e o site-packages
                # do usuário, e não coloca a pasta atual no sys.path.
                [sys.executable, "-I", "-c", codigo + _RODAPE],
                input=json.dumps(grades),
                capture_output=True,
                text=True,
                timeout=limite_segundos,
                cwd=pasta,
            )
        except subprocess.TimeoutExpired:
            return ResultadoExecucao(None, f"tempo esgotado ({limite_segundos:g} s)")

    if processo.returncode != 0:
        # A última linha do stderr costuma ser a exceção, por exemplo
        # "IndexError: list index out of range".
        linhas = processo.stderr.strip().splitlines()
        return ResultadoExecucao(None, linhas[-1] if linhas else f"código de saída {processo.returncode}")

    linhas = processo.stdout.strip().splitlines()
    try:
        saidas = json.loads(linhas[-1])
    except (IndexError, json.JSONDecodeError):
        return ResultadoExecucao(None, "o programa não imprimiu uma lista de grades válida")
    return ResultadoExecucao(saidas, None)
