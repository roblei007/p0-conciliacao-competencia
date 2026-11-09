import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import httpx
from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    InternalServerError,
    OpenAIError,
    PermissionDeniedError,
    RateLimitError,
)

import app_basico


CONFIGURACAO = {
    "LLM_API_URL": "https://api.groq.com/openai/v1",
    "LLM_MODEL": "qwen/qwen3.8-27b",
    "GROQ_API_KEY": "chave-de-teste",
}


def erro_status(tipo: type[APIStatusError], status: int) -> APIStatusError:
    requisicao = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    resposta = httpx.Response(status, request=requisicao)
    return tipo("erro simulado", response=resposta, body=None)


class ConsultarLlmTests(unittest.TestCase):
    def test_chamada_sdk_e_texto_de_resposta(self) -> None:
        resposta = SimpleNamespace(
            choices=[
                SimpleNamespace(
                    finish_reason="stop",
                    message=SimpleNamespace(content="  resposta de teste  "),
                )
            ]
        )
        with (
            patch.dict(os.environ, CONFIGURACAO, clear=True),
            patch("app_basico.OpenAI") as cliente_cls,
        ):
            cliente_cls.return_value.chat.completions.create.return_value = resposta

            resultado = app_basico.consultar_llm("fato de teste")

        self.assertEqual(resultado, "resposta de teste")
        cliente_cls.assert_called_once_with(
            base_url=CONFIGURACAO["LLM_API_URL"],
            api_key=CONFIGURACAO["GROQ_API_KEY"],
            timeout=120,
        )
        cliente_cls.return_value.chat.completions.create.assert_called_once_with(
            model=CONFIGURACAO["LLM_MODEL"],
            messages=[
                {"role": "system", "content": app_basico.SYSTEM_PROMPT},
                {"role": "user", "content": "fato de teste"},
            ],
            max_tokens=1000,
        )

    def test_variaveis_obrigatorias(self) -> None:
        for variavel in CONFIGURACAO:
            with self.subTest(variavel=variavel):
                ambiente = CONFIGURACAO | {variavel: ""}
                with (
                    patch.dict(os.environ, ambiente, clear=True),
                    patch("app_basico.OpenAI") as cliente_cls,
                    self.assertRaises(app_basico.ConfigurationError),
                ):
                    app_basico.consultar_llm("fato")
                cliente_cls.assert_not_called()

    def test_timeout_e_limite_de_tokens_devem_ser_inteiros_positivos(self) -> None:
        for variavel, valor in (
            ("LLM_TIMEOUT", "abc"),
            ("LLM_TIMEOUT", "0"),
            ("LLM_TIMEOUT", "-1"),
            ("LLM_MAX_TOKENS", "abc"),
            ("LLM_MAX_TOKENS", "0"),
            ("LLM_MAX_TOKENS", "-1"),
        ):
            with self.subTest(variavel=variavel, valor=valor):
                ambiente = CONFIGURACAO | {variavel: valor}
                with (
                    patch.dict(os.environ, ambiente, clear=True),
                    patch("app_basico.OpenAI") as cliente_cls,
                ):
                    with self.assertRaisesRegex(app_basico.ConfigurationError, variavel):
                        app_basico.consultar_llm("fato")
                cliente_cls.assert_not_called()

    def test_resposta_vazia_sem_choices_ou_sem_texto_e_rejeitada(self) -> None:
        respostas = (
            SimpleNamespace(choices=[]),
            SimpleNamespace(
                choices=[
                    SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content=None))
                ]
            ),
            SimpleNamespace(
                choices=[
                    SimpleNamespace(finish_reason="stop", message=SimpleNamespace(content="  "))
                ]
            ),
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        finish_reason="length",
                        message=SimpleNamespace(content="resposta parcial"),
                    )
                ]
            ),
        )
        for resposta in respostas:
            with self.subTest(resposta=resposta):
                with (
                    patch.dict(os.environ, CONFIGURACAO, clear=True),
                    patch("app_basico.OpenAI") as cliente_cls,
                ):
                    cliente_cls.return_value.chat.completions.create.return_value = resposta
                    with self.assertRaises(app_basico.InvalidResponseError):
                        app_basico.consultar_llm("fato")


class ClassificarErroTests(unittest.TestCase):
    def test_erros_de_autenticacao_e_permissao(self) -> None:
        for tipo in (AuthenticationError, PermissionDeniedError):
            with self.subTest(tipo=tipo):
                erro = erro_status(tipo, 401 if tipo is AuthenticationError else 403)
                self.assertEqual(app_basico._classificar_erro_api(erro)[0], 3)

    def test_conexao_limite_e_indisponibilidade(self) -> None:
        requisicao = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
        erros = (
            APIConnectionError(request=requisicao),
            erro_status(RateLimitError, 429),
            erro_status(InternalServerError, 500),
        )
        for erro in erros:
            with self.subTest(tipo=type(erro).__name__):
                self.assertEqual(app_basico._classificar_erro_api(erro)[0], 4)

    def test_outros_status_e_erros_do_sdk(self) -> None:
        self.assertEqual(app_basico._classificar_erro_api(erro_status(APIStatusError, 400))[0], 2)
        self.assertEqual(app_basico._classificar_erro_api(OpenAIError("erro"))[0], 99)


class MainTests(unittest.TestCase):
    def test_sucesso(self) -> None:
        with (
            patch("app_basico.load_dotenv"),
            patch("builtins.input", return_value="fato"),
            patch("app_basico.consultar_llm", return_value="resposta"),
            patch("builtins.print") as print_mock,
        ):
            self.assertEqual(app_basico.main(), 0)
        print_mock.assert_called_once_with("resposta")

    def test_entrada_vazia_ou_fim_de_entrada(self) -> None:
        for entrada in ("", "   "):
            with self.subTest(entrada=entrada):
                with (
                    patch("app_basico.load_dotenv"),
                    patch("builtins.input", return_value=entrada),
                    patch("app_basico.consultar_llm") as consultar_mock,
                    patch("builtins.print"),
                ):
                    self.assertEqual(app_basico.main(), 1)
                consultar_mock.assert_not_called()

        with (
            patch("app_basico.load_dotenv"),
            patch("builtins.input", side_effect=EOFError),
            patch("builtins.print"),
        ):
            self.assertEqual(app_basico.main(), 1)

    def test_erros_de_configuracao_e_resposta_usam_codigos_corretos(self) -> None:
        casos = (
            (app_basico.ConfigurationError("configuração inválida"), 2),
            (app_basico.InvalidResponseError("resposta vazia"), 5),
        )
        for erro, codigo in casos:
            with self.subTest(codigo=codigo):
                with (
                    patch("app_basico.load_dotenv"),
                    patch("builtins.input", return_value="fato"),
                    patch("app_basico.consultar_llm", side_effect=erro),
                    patch("builtins.print"),
                ):
                    self.assertEqual(app_basico.main(), codigo)

    def test_erros_da_api_usam_codigos_corretos(self) -> None:
        casos = (
            (erro_status(AuthenticationError, 401), 3),
            (erro_status(RateLimitError, 429), 4),
            (erro_status(APIStatusError, 400), 2),
            (OpenAIError("erro"), 99),
        )
        for erro, codigo in casos:
            with self.subTest(codigo=codigo):
                with (
                    patch("app_basico.load_dotenv"),
                    patch("builtins.input", return_value="fato"),
                    patch("app_basico.consultar_llm", side_effect=erro),
                    patch("builtins.print"),
                ):
                    self.assertEqual(app_basico.main(), codigo)


if __name__ == "__main__":
    unittest.main()
