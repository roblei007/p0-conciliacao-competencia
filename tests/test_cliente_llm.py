import unittest
from dataclasses import replace
from unittest.mock import patch

import requests

from lancamentos.cliente_llm import chamar_llm, extrair_texto
from lancamentos.erros import (
    ErroAutenticacao,
    ErroComunicacao,
    ErroResposta,
    ErroServicoIndisponivel,
)
from tests.auxiliares import CHAVE_FALSA, CONFIG, corpo_texto, resposta_http

ALVO = "lancamentos.cliente_llm.requests.post"


class TestChamarLLM(unittest.TestCase):
    def test_sucesso_devolve_texto_e_envia_chave_no_cabecalho(self):
        with patch(ALVO, return_value=resposta_http(200, corpo_texto("olá"))) as post:
            self.assertEqual(chamar_llm({"a": 1}, CONFIG), "olá")
        enviado = post.call_args.kwargs
        self.assertEqual(enviado["headers"]["x-api-key"], CHAVE_FALSA)
        self.assertEqual(enviado["timeout"], CONFIG.timeout)

    def test_credencial_invalida(self):
        for status in (401, 403):
            with self.subTest(status=status):
                with patch(ALVO, return_value=resposta_http(status)):
                    with self.assertRaises(ErroAutenticacao) as ctx:
                        chamar_llm({}, CONFIG)
                self.assertNotIn(CHAVE_FALSA, str(ctx.exception))

    def test_403_menciona_possivel_bloqueio_de_rede(self):
        with patch(ALVO, return_value=resposta_http(403)):
            with self.assertRaises(ErroAutenticacao) as ctx:
                chamar_llm({}, CONFIG)
        self.assertIn("proxy", str(ctx.exception))

    def test_servico_indisponivel(self):
        for status in (429, 500, 503, 529):
            with self.subTest(status=status):
                with patch(ALVO, return_value=resposta_http(status)):
                    with self.assertRaises(ErroServicoIndisponivel):
                        chamar_llm({}, CONFIG)

    def test_requisicao_rejeitada_mostra_detalhe_da_api(self):
        corpo = {"error": {"message": "modelo inexistente"}}
        with patch(ALVO, return_value=resposta_http(400, corpo)):
            with self.assertRaises(ErroComunicacao) as ctx:
                chamar_llm({}, CONFIG)
        self.assertIn("modelo inexistente", str(ctx.exception))

    def test_timeout(self):
        with patch(ALVO, side_effect=requests.exceptions.Timeout()):
            with self.assertRaises(ErroComunicacao) as ctx:
                chamar_llm({}, CONFIG)
        self.assertIn("segundos", str(ctx.exception))

    def test_falha_de_conexao(self):
        with patch(ALVO, side_effect=requests.exceptions.ConnectionError("DNS")):
            with self.assertRaises(ErroComunicacao) as ctx:
                chamar_llm({}, CONFIG)
        self.assertIn("conexão", str(ctx.exception))

    def test_corpo_nao_json(self):
        with patch(ALVO, return_value=resposta_http(200, json_invalido=True)):
            with self.assertRaises(ErroResposta):
                chamar_llm({}, CONFIG)


class TestExtrairTexto(unittest.TestCase):
    def test_concatena_blocos_de_texto(self):
        dados = {"content": [{"type": "text", "text": "a"}, {"type": "text", "text": "b"}]}
        self.assertEqual(extrair_texto(dados), "ab")

    def test_formatos_inesperados_e_resposta_vazia(self):
        casos = [None, [], {}, {"content": "x"}, {"content": []}, {"content": [{"type": "text", "text": "  "}]}]
        for dados in casos:
            with self.subTest(dados=dados):
                with self.assertRaises(ErroResposta):
                    extrair_texto(dados)

    def test_resposta_truncada_por_max_tokens(self):
        with self.assertRaises(ErroResposta) as ctx:
            extrair_texto(corpo_texto("{", stop_reason="max_tokens"))
        self.assertIn("LLM_MAX_TOKENS", str(ctx.exception))


CONFIG_OPENAI = replace(CONFIG, formato="openai", api_url="https://gateway.exemplo/v1/chat/completions")


def corpo_openai(texto, finish_reason="stop"):
    return {"choices": [{"message": {"role": "assistant", "content": texto}, "finish_reason": finish_reason}]}


class TestFormatoOpenAI(unittest.TestCase):
    def test_sucesso_usa_bearer_e_le_choices(self):
        with patch(ALVO, return_value=resposta_http(200, corpo_openai("olá"))) as post:
            self.assertEqual(chamar_llm({"a": 1}, CONFIG_OPENAI), "olá")
        cab = post.call_args.kwargs["headers"]
        self.assertEqual(cab["Authorization"], f"Bearer {CHAVE_FALSA}")
        self.assertNotIn("x-api-key", cab)

    def test_resposta_truncada(self):
        with self.assertRaises(ErroResposta) as ctx:
            extrair_texto(corpo_openai("{", finish_reason="length"), "openai")
        self.assertIn("LLM_MAX_TOKENS", str(ctx.exception))

    def test_formatos_inesperados_e_vazio(self):
        for dados in (None, {}, {"choices": []}, {"choices": [{}]}, corpo_openai("  "), corpo_openai(None)):
            with self.subTest(dados=dados):
                with self.assertRaises(ErroResposta):
                    extrair_texto(dados, "openai")

    def test_autenticacao_igual_ao_outro_formato(self):
        with patch(ALVO, return_value=resposta_http(401)):
            with self.assertRaises(ErroAutenticacao):
                chamar_llm({}, CONFIG_OPENAI)


if __name__ == "__main__":
    unittest.main()
