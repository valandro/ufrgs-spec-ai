"""Cliente do Gemini: pausa entre chamadas, retentativas e contagem de tokens."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Protocol

from google import genai
from google.genai import errors, types

log = logging.getLogger(__name__)

# Erros temporários: limite da chave gratuita (429) e falhas do servidor (5xx).
# Repetir vale a pena. Erros como 400 (pedido inválido) ou 403 (chave inválida)
# falham de novo do mesmo jeito, então o solver desiste na hora.
_CODIGOS_TEMPORARIOS = {429, 500, 502, 503, 504}


@dataclass(frozen=True)
class RespostaLLM:
    texto: str
    tokens_entrada: int     # tamanho do prompt
    tokens_raciocinio: int  # tokens de "pensamento" antes da resposta final
    tokens_saida: int       # tamanho da resposta final
    segundos: float         # duração da chamada que deu certo, sem as esperas
    tentativas: int


class ModeloLinguagem(Protocol):
    """Qualquer objeto com gerar(prompt) serve. Nos testes, usamos um modelo falso.

    Os atributos modelo e raciocinio vão para cada linha de resultado, para que
    os arquivos em resultados/ mostrem a configuração que gerou cada número.
    """

    modelo: str
    raciocinio: str

    def gerar(self, prompt: str) -> RespostaLLM: ...


class ClienteGemini:
    def __init__(
        self,
        chave: str,
        modelo: str = "gemini-3.5-flash-lite",
        raciocinio: str = "high",
        pausa_segundos: float = 1.0,
        max_tentativas: int = 5,
        espera_inicial: float = 10.0,
    ) -> None:
        self._cliente = genai.Client(api_key=chave)
        self.modelo = modelo
        self.raciocinio = raciocinio
        self._pausa = pausa_segundos
        self._max_tentativas = max_tentativas
        self._espera_inicial = espera_inicial
        self._ultima_chamada = 0.0

    def _respeitar_pausa(self) -> None:
        # Espera só o que falta para completar a pausa desde a última chamada.
        # Se o código gerado levou 3 s para rodar, não há espera extra.
        decorrido = time.monotonic() - self._ultima_chamada
        if decorrido < self._pausa:
            time.sleep(self._pausa - decorrido)

    def gerar(self, prompt: str) -> RespostaLLM:
        config = types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level=self.raciocinio),
        )
        for tentativa in range(1, self._max_tentativas + 1):
            self._respeitar_pausa()
            inicio = time.perf_counter()
            try:
                resposta = self._cliente.models.generate_content(
                    model=self.modelo, contents=prompt, config=config
                )
            except errors.APIError as erro:
                self._ultima_chamada = time.monotonic()
                temporario = erro.code in _CODIGOS_TEMPORARIOS
                if not temporario or tentativa == self._max_tentativas:
                    raise
                # Espera exponencial: 10, 20, 40, 80 s. Isso dá tempo para a
                # cota por minuto da chave gratuita se renovar.
                espera = self._espera_inicial * 2 ** (tentativa - 1)
                log.warning("Erro %s do Gemini. Tentativa %d de %d em %.0f s.",
                            erro.code, tentativa + 1, self._max_tentativas, espera)
                time.sleep(espera)
                continue

            self._ultima_chamada = time.monotonic()
            uso = resposta.usage_metadata
            return RespostaLLM(
                texto=resposta.text or "",
                tokens_entrada=(uso.prompt_token_count or 0) if uso else 0,
                tokens_raciocinio=(uso.thoughts_token_count or 0) if uso else 0,
                tokens_saida=(uso.candidates_token_count or 0) if uso else 0,
                segundos=time.perf_counter() - inicio,
                tentativas=tentativa,
            )
        raise RuntimeError("inalcançável")  # o laço sempre retorna ou lança
