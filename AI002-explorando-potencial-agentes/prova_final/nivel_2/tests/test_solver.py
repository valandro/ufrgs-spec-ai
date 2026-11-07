"""Testes sem chamar a API: um modelo falso devolve respostas fixas.

Rodar: python -m unittest discover -s tests -v
"""

import json
import tempfile
import unittest
from pathlib import Path

from solver.abordagens import extrair_codigo, extrair_json, resolver_codigo, resolver_fim_a_fim
from solver.executor import executar
from solver.llm import RespostaLLM
from solver.main import ConfiguracaoMisturada, carregar_tarefas, escrever_resumo, executar_experimento

RAIZ = Path(__file__).resolve().parent.parent
TAREFAS = {t[0]: t for t in carregar_tarefas(RAIZ / "tarefas" / "tarefas.txt")}


class ModeloFalso:
    """Devolve sempre o mesmo texto e conta quantas vezes foi chamado."""

    def __init__(self, texto: str, raciocinio: str = "high") -> None:
        self.texto = texto
        self.chamadas = 0
        self.modelo = "modelo-falso"
        self.raciocinio = raciocinio

    def gerar(self, prompt: str) -> RespostaLLM:
        self.chamadas += 1
        return RespostaLLM(self.texto, tokens_entrada=100, tokens_raciocinio=50,
                           tokens_saida=10, segundos=0.1, tentativas=1)


# 25ff71a9: a figura desce uma linha.
CODIGO_CORRETO_25FF = """```python
def transform(grid):
    return [[0] * len(grid[0])] + [linha[:] for linha in grid[:-1]]
```"""

# Programa que decora os exemplos de treino: acerta o treino e erra o teste.
CODIGO_DECORADO = """```python
TABELA = {TABELA}
def transform(grid):
    return TABELA.get(str(grid), [[0]])
```"""


class TestExtracao(unittest.TestCase):
    def test_json_com_cerca_e_texto_em_volta(self):
        texto = 'Aqui está:\n```json\n{"test": [{"output": [[1]]}]}\n```\nFim.'
        self.assertEqual(extrair_json(texto), {"test": [{"output": [[1]]}]})

    def test_json_invalido(self):
        with self.assertRaises(ValueError):
            extrair_json("não sei resolver")

    def test_codigo_com_e_sem_cerca(self):
        self.assertEqual(extrair_codigo("```python\nx = 1\n```"), "x = 1\n")
        self.assertEqual(extrair_codigo("x = 1"), "x = 1")


class TestExecutor(unittest.TestCase):
    def test_tempo_esgotado(self):
        r = executar("def transform(g):\n    while True: pass", [[[1]]], limite_segundos=1)
        self.assertIsNone(r.saidas)
        self.assertIn("tempo esgotado", r.erro)

    def test_excecao(self):
        r = executar("def transform(g): return 1 / 0", [[[1]]])
        self.assertIn("ZeroDivisionError", r.erro)

    def test_print_de_depuracao_nao_atrapalha(self):
        r = executar("def transform(g):\n    print('debug')\n    return g", [[[1, 2]]])
        self.assertEqual(r.saidas, [[[1, 2]]])


class TestAbordagens(unittest.TestCase):
    def test_fim_a_fim_correto(self):
        tid, conj, tarefa = TAREFAS["25ff71a9"]
        resposta = json.dumps({"rule": "x", "test": [{"output": t["output"]} for t in tarefa["test"]]})
        r, _ = resolver_fim_a_fim(ModeloFalso(resposta), tid, conj, tarefa)
        self.assertTrue(r.resolvida)
        self.assertEqual((r.tokens_entrada, r.tokens_raciocinio, r.tokens_saida), (100, 50, 10))

    def test_fim_a_fim_formato_invalido(self):
        tid, conj, tarefa = TAREFAS["25ff71a9"]
        r, _ = resolver_fim_a_fim(ModeloFalso("[[1, 2]]"), tid, conj, tarefa)
        self.assertFalse(r.resolvida)
        self.assertEqual(r.erro, "resposta fora do formato JSON")

    def test_codigo_correto(self):
        tid, conj, tarefa = TAREFAS["25ff71a9"]
        r, codigo = resolver_codigo(ModeloFalso(CODIGO_CORRETO_25FF), tid, conj, tarefa)
        self.assertTrue(r.treino_ok)
        self.assertTrue(r.resolvida)
        self.assertIn("def transform", codigo)

    def test_codigo_acerta_treino_e_erra_teste(self):
        tid, conj, tarefa = TAREFAS["44f52bb0"]
        tabela = {str(p["input"]): p["output"] for p in tarefa["train"]}
        r, _ = resolver_codigo(ModeloFalso(CODIGO_DECORADO.replace("{TABELA}", repr(tabela))), tid, conj, tarefa)
        self.assertTrue(r.treino_ok)
        self.assertFalse(r.resolvida)

    def test_codigo_que_quebra(self):
        tid, conj, tarefa = TAREFAS["25ff71a9"]
        r, _ = resolver_codigo(ModeloFalso("```python\ndef transform(g) return g\n```"), tid, conj, tarefa)
        self.assertFalse(r.treino_ok)
        self.assertFalse(r.resolvida)
        self.assertIn("SyntaxError", r.erro)


class TestExperimento(unittest.TestCase):
    def test_retoma_sem_repetir_chamadas_e_resume(self):
        tarefas = [TAREFAS["25ff71a9"], TAREFAS["44f52bb0"]]
        modelo = ModeloFalso(CODIGO_CORRETO_25FF)
        with tempfile.TemporaryDirectory() as pasta:
            saida = Path(pasta)
            executar_experimento(modelo, tarefas, ["codigo"], saida, 10.0)
            self.assertEqual(modelo.chamadas, 2)
            # Segunda execução: tudo já está no CSV, então nenhuma chamada nova.
            executar_experimento(modelo, tarefas, ["codigo"], saida, 10.0)
            self.assertEqual(modelo.chamadas, 2)

            [resumo] = escrever_resumo(saida)
            self.assertEqual(resumo["tarefas"], 2)
            self.assertEqual(resumo["resolvidas"], 1)  # só 25ff71a9
            self.assertEqual(resumo["treino_ok"], 1)
            self.assertEqual(resumo["tokens_raciocinio"], 100)
            self.assertTrue((saida / "respostas" / "codigo" / "25ff71a9.py").exists())
            self.assertEqual((resumo["modelo"], resumo["raciocinio"]), ("modelo-falso", "high"))

    def test_recusa_misturar_niveis_de_raciocinio(self):
        tarefas = [TAREFAS["25ff71a9"], TAREFAS["44f52bb0"]]
        with tempfile.TemporaryDirectory() as pasta:
            saida = Path(pasta)
            executar_experimento(ModeloFalso(CODIGO_CORRETO_25FF), tarefas[:1], ["codigo"], saida, 10.0)
            # Retomar com outro nível não pode somar linhas das duas configurações.
            outro = ModeloFalso(CODIGO_CORRETO_25FF, raciocinio="minimal")
            with self.assertRaises(ConfiguracaoMisturada):
                executar_experimento(outro, tarefas, ["codigo"], saida, 10.0)
            self.assertEqual(outro.chamadas, 0)


if __name__ == "__main__":
    unittest.main()
