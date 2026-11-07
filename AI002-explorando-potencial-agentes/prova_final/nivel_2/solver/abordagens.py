"""As duas abordagens: fim a fim e geração de código.

Os prompts são os mesmos do notebook do nível 1. Assim, a diferença de
resultado entre os níveis vem do solver, e não de um prompt diferente.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass

from .executor import Grade, executar
from .llm import ModeloLinguagem

PROMPT_FIM_A_FIM = """Solve this ARC-AGI-1 task. Infer the transformation from the training
input/output pairs, then apply it to each test input. Grids are lists of rows of
integers from 0 to 9, each integer is a color. The output size can differ from the input size.
Return only a JSON object in this format, without Markdown:
{"rule": "Short description of the rule.", "test": [{"output": [[0, 1], [2, 3]]}]}
Include one output grid for every test input, in the same order.

"""

PROMPT_CODIGO = """Solve this ARC-AGI-1 task by writing a Python program. Infer the transformation
from the training input/output pairs. Grids are lists of rows of integers from 0 to 9,
each integer is a color. The output size can differ from the input size.
Write a function transform(grid) that receives one input grid and returns the output grid
as a list of lists of integers. Use only the Python standard library.
Return only the code, inside a single ```python code block.

"""


@dataclass
class ResultadoTarefa:
    """Uma linha do resumo: o resultado de uma tarefa em uma abordagem."""

    tarefa: str
    conjunto: str
    abordagem: str
    modelo: str
    raciocinio: str
    resolvida: bool
    treino_ok: bool | None  # só faz sentido na geração de código
    erro: str
    tokens_entrada: int
    tokens_raciocinio: int
    tokens_saida: int
    segundos: float
    tentativas_api: int


def montar_tarefa(tarefa: dict) -> str:
    """Exemplos de treino completos e apenas as entradas de teste.

    As respostas de teste nunca entram no prompt. Se entrassem, o modelo
    poderia copiá-las, e o experimento mediria memória, não raciocínio.
    """
    visivel = {"train": tarefa["train"], "test": [{"input": t["input"]} for t in tarefa["test"]]}
    return json.dumps(visivel)


def extrair_json(texto: str) -> dict:
    """Lê o JSON da resposta, tolerando cercas de Markdown e texto em volta."""
    texto = texto.strip()
    cerca = re.search(r"```(?:json)?\s*\n(.*?)```", texto, flags=re.S)
    if cerca:
        texto = cerca.group(1)
    inicio, fim = texto.find("{"), texto.rfind("}")
    if inicio == -1 or fim == -1:
        raise ValueError("nenhum objeto JSON na resposta")
    return json.loads(texto[inicio : fim + 1])


def extrair_codigo(texto: str) -> str:
    """Pega o primeiro bloco ```python. Sem bloco, usa o texto inteiro."""
    blocos = re.findall(r"```(?:python|py)?[ \t]*\n(.*?)```", texto, flags=re.S)
    return blocos[0] if blocos else texto


def _base(tarefa_id: str, conjunto: str, abordagem: str, modelo: ModeloLinguagem, resposta) -> ResultadoTarefa:
    return ResultadoTarefa(
        tarefa=tarefa_id, conjunto=conjunto, abordagem=abordagem,
        # Vêm do cliente que fez a chamada, e não de uma constante, para não divergirem.
        modelo=modelo.modelo, raciocinio=modelo.raciocinio,
        resolvida=False, treino_ok=None, erro="",
        tokens_entrada=resposta.tokens_entrada,
        tokens_raciocinio=resposta.tokens_raciocinio,
        tokens_saida=resposta.tokens_saida,
        segundos=resposta.segundos,
        tentativas_api=resposta.tentativas,
    )


def resolver_fim_a_fim(
    modelo: ModeloLinguagem, tarefa_id: str, conjunto: str, tarefa: dict
) -> tuple[ResultadoTarefa, str]:
    """Pede a grade de saída diretamente. Devolve o resultado e a resposta bruta."""
    resposta = modelo.gerar(PROMPT_FIM_A_FIM + montar_tarefa(tarefa))
    resultado = _base(tarefa_id, conjunto, "fim_a_fim", modelo, resposta)
    esperadas = [t["output"] for t in tarefa["test"]]
    try:
        obtidas = [t["output"] for t in extrair_json(resposta.texto)["test"]]
    except (ValueError, KeyError, TypeError):
        # JSONDecodeError é subclasse de ValueError.
        resultado.erro = "resposta fora do formato JSON"
        return resultado, resposta.texto
    # Comparação exata da grade inteira, que é o critério do ARC.
    resultado.resolvida = obtidas == esperadas
    if len(obtidas) != len(esperadas):
        resultado.erro = f"{len(obtidas)} grades para {len(esperadas)} entradas de teste"
    return resultado, resposta.texto


def resolver_codigo(
    modelo: ModeloLinguagem, tarefa_id: str, conjunto: str, tarefa: dict,
    limite_segundos: float = 10.0,
) -> tuple[ResultadoTarefa, str]:
    """Pede transform(grid), roda no treino e no teste. Devolve o resultado e o código."""
    resposta = modelo.gerar(PROMPT_CODIGO + montar_tarefa(tarefa))
    resultado = _base(tarefa_id, conjunto, "codigo", modelo, resposta)
    codigo = extrair_codigo(resposta.texto)

    inicio = time.perf_counter()
    # 1) Treino: verifica se o programa reproduz todos os exemplos conhecidos.
    treino = executar(codigo, [p["input"] for p in tarefa["train"]], limite_segundos)
    resultado.treino_ok = treino.saidas == [p["output"] for p in tarefa["train"]]
    # 2) Teste: roda mesmo se o treino falhou. O nível 2 mede as duas coisas
    #    separadamente, e o caso "acerta o treino, erra o teste" interessa ao relatório.
    teste = executar(codigo, [t["input"] for t in tarefa["test"]], limite_segundos)
    resultado.resolvida = teste.saidas == [t["output"] for t in tarefa["test"]]
    # O tempo da tarefa inclui a execução do código, como pede o enunciado.
    resultado.segundos += time.perf_counter() - inicio

    erros = []
    if treino.erro:
        erros.append(f"treino: {treino.erro}")
    if teste.erro:
        erros.append(f"teste: {teste.erro}")
    resultado.erro = "; ".join(erros)
    return resultado, codigo
