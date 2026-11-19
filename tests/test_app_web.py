import unittest
from unittest.mock import patch

import httpx
from openai import APIConnectionError

import app_web


class AplicacaoWebTests(unittest.TestCase):
    def setUp(self) -> None:
        app_web.app.config.update(TESTING=True)
        self.cliente = app_web.app.test_client()

    def test_pagina_inicial_exibe_formulario_e_portal_atual(self) -> None:
        resposta = self.cliente.get("/")

        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b'name="fato"', resposta.data)
        self.assertIn(b"https://devel-llm.eastus.cloudapp.azure.com/", resposta.data)

    def test_envio_vazio_mostra_erro_de_validacao(self) -> None:
        resposta = self.cliente.post("/", data={"fato": "  "})

        self.assertEqual(resposta.status_code, 400)
        self.assertIn(b"Descreva o fato operacional.", resposta.data)

    def test_envio_gera_e_exibe_sugestao(self) -> None:
        with patch("app_web.consultar_llm", return_value="Sugestao de lancamento"):
            resposta = self.cliente.post("/", data={"fato": "Fatura de energia"})

        self.assertEqual(resposta.status_code, 200)
        self.assertIn(b"Sugestao de lancamento", resposta.data)

    def test_falha_do_servico_e_exibida_sem_encerrar_a_aplicacao(self) -> None:
        erro = APIConnectionError(request=httpx.Request("POST", "https://llm-internal.softex"))
        with patch("app_web.consultar_llm", side_effect=erro):
            resposta = self.cliente.post("/", data={"fato": "Fatura de energia"})

        self.assertEqual(resposta.status_code, 503)
        self.assertIn(b"Falha de conex", resposta.data)


if __name__ == "__main__":
    unittest.main()
