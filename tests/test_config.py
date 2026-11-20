import unittest

from lancamentos.config import carregar_configuracao
from lancamentos.erros import ErroConfiguracao, ErroCredencialAusente

BASE = {"LLM_API_KEY": "abc", "LLM_MODEL": "modelo-x"}


class TestConfiguracao(unittest.TestCase):
    def test_configuracao_minima_usa_padroes(self):
        cfg = carregar_configuracao(BASE)
        self.assertEqual(cfg.modelo, "modelo-x")
        self.assertEqual(cfg.max_tokens, 1500)
        self.assertEqual(cfg.timeout, 30.0)
        self.assertTrue(cfg.api_url.startswith("https://"))

    def test_parametros_podem_ser_alterados_pelo_ambiente(self):
        cfg = carregar_configuracao(
            {**BASE, "LLM_MAX_TOKENS": "800", "LLM_TEMPERATURE": "0.3", "LLM_TIMEOUT": "10"}
        )
        self.assertEqual((cfg.max_tokens, cfg.temperatura, cfg.timeout), (800, 0.3, 10.0))

    def test_credencial_ausente(self):
        for env in ({}, {"LLM_MODEL": "m"}, {"LLM_API_KEY": "  ", "LLM_MODEL": "m"}):
            with self.subTest(env=env):
                with self.assertRaises(ErroCredencialAusente):
                    carregar_configuracao(env)

    def test_modelo_ausente(self):
        with self.assertRaises(ErroConfiguracao):
            carregar_configuracao({"LLM_API_KEY": "abc"})

    def test_valores_invalidos(self):
        invalidos = [
            {"LLM_MAX_TOKENS": "muitos"},
            {"LLM_MAX_TOKENS": "0"},
            {"LLM_TEMPERATURE": "2"},
            {"LLM_TIMEOUT": "-5"},
            {"LLM_API_URL": "ftp://servidor"},
            {"LOG_LEVEL": "TUDO"},
        ]
        for extra in invalidos:
            with self.subTest(extra=extra):
                with self.assertRaises(ErroConfiguracao):
                    carregar_configuracao({**BASE, **extra})

    def test_formato_padrao_e_anthropic(self):
        self.assertEqual(carregar_configuracao(BASE).formato, "anthropic")

    def test_formato_openai_exige_url(self):
        with self.assertRaises(ErroConfiguracao) as ctx:
            carregar_configuracao({**BASE, "LLM_API_FORMAT": "openai"})
        self.assertIn("LLM_API_URL", str(ctx.exception))
        cfg = carregar_configuracao(
            {**BASE, "LLM_API_FORMAT": "openai", "LLM_API_URL": "https://gateway.exemplo/v1/chat/completions"}
        )
        self.assertEqual(cfg.formato, "openai")

    def test_formato_desconhecido(self):
        with self.assertRaises(ErroConfiguracao):
            carregar_configuracao({**BASE, "LLM_API_FORMAT": "outro"})

    def test_chave_nao_aparece_em_repr(self):
        cfg = carregar_configuracao({**BASE, "LLM_API_KEY": "SEGREDO-XYZ"})
        self.assertNotIn("SEGREDO-XYZ", repr(cfg))
        self.assertNotIn("SEGREDO-XYZ", str(cfg))


if __name__ == "__main__":
    unittest.main()
