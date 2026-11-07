"""Testa as retentativas do cliente com um cliente HTTP falso, sem rede."""

import unittest
from types import SimpleNamespace
from unittest import mock

from google.genai import errors

from solver.llm import ClienteGemini


def resposta_ok():
    uso = SimpleNamespace(prompt_token_count=10, thoughts_token_count=20, candidates_token_count=3)
    return SimpleNamespace(text="ok", usage_metadata=uso)


def cliente_com(efeitos):
    cliente = ClienteGemini("chave-falsa", pausa_segundos=0, espera_inicial=0.01)
    cliente._cliente = mock.Mock()
    cliente._cliente.models.generate_content.side_effect = efeitos
    return cliente


class TestRetentativas(unittest.TestCase):
    def test_repete_apos_429(self):
        c = cliente_com([errors.APIError(429, {}), errors.APIError(503, {}), resposta_ok()])
        r = c.gerar("p")
        self.assertEqual(r.tentativas, 3)
        self.assertEqual((r.tokens_entrada, r.tokens_raciocinio, r.tokens_saida), (10, 20, 3))

    def test_nao_repete_erro_permanente(self):
        c = cliente_com([errors.APIError(403, {}), resposta_ok()])
        with self.assertRaises(errors.APIError):
            c.gerar("p")
        self.assertEqual(c._cliente.models.generate_content.call_count, 1)

    def test_desiste_apos_maximo(self):
        c = cliente_com([errors.APIError(429, {})] * 5)
        with self.assertRaises(errors.APIError):
            c.gerar("p")
        self.assertEqual(c._cliente.models.generate_content.call_count, 5)


if __name__ == "__main__":
    unittest.main()
