import io
import logging
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from lancamentos.erros import ErroAutenticacao, ErroComunicacao
from lancamentos.main import executar, main
from tests.auxiliares import CHAVE_FALSA, CONFIG, RESPOSTA_JSON_OK

ENV_VALIDO = {"LLM_API_KEY": CHAVE_FALSA, "LLM_MODEL": "modelo-teste", "LOG_ARQUIVO": os.devnull}


def rodar(argv, env, chamar=None):
    """Executa main() capturando saída; isola do .env real e da rede."""
    saida, erro = io.StringIO(), io.StringIO()
    try:
        with patch.dict(os.environ, env, clear=True), patch("lancamentos.config.load_dotenv"), \
                redirect_stdout(saida), redirect_stderr(erro):
            if chamar is None:
                codigo = main(argv)
            else:
                with patch("lancamentos.main.chamar_llm", chamar):
                    codigo = main(argv)
    finally:
        # fecha (e descarrega) os arquivos de log abertos por main(), isolando os testes
        logger = logging.getLogger("lancamentos")
        for h in [h for h in logger.handlers if getattr(h, "_lancamentos", False)]:
            logger.removeHandler(h)
            h.close()
    return codigo, saida.getvalue(), erro.getvalue()


class TestExecutar(unittest.TestCase):
    def test_fluxo_completo_com_resposta_simulada(self):
        saida = executar("fatura de energia", CONFIG, chamar=lambda s, c: RESPOSTA_JSON_OK)
        self.assertIn("Despesa com energia elétrica", saida)
        self.assertIn("R$ 12.400,00", saida)

    def test_erro_simulado_propaga_erro_controlado(self):
        def falha(_s, _c):
            raise ErroComunicacao("sem rede")

        with self.assertRaises(ErroComunicacao):
            executar("x", CONFIG, chamar=falha)


class TestMain(unittest.TestCase):
    def test_sucesso(self):
        codigo, saida, erro = rodar(["--texto", "fatura de energia"], ENV_VALIDO,
                                    chamar=lambda s, c: RESPOSTA_JSON_OK)
        self.assertEqual(codigo, 0)
        self.assertIn("Lançamento 1", saida)
        self.assertEqual(erro, "")

    def test_entrada_vazia_nao_chama_llm_nem_exige_configuracao(self):
        chamadas = []
        codigo, saida, erro = rodar(["--texto", "   "], {}, chamar=lambda s, c: chamadas.append(1))
        self.assertEqual(codigo, 1)
        self.assertIn("Entrada vazia", erro)
        self.assertEqual(chamadas, [])

    def test_credencial_ausente(self):
        codigo, _, erro = rodar(["--texto", "fato"], {"LLM_MODEL": "m"})
        self.assertEqual(codigo, 2)
        self.assertIn("LLM_API_KEY", erro)

    def test_credencial_invalida_termina_de_forma_controlada_sem_expor_chave(self):
        def recusa(_s, _c):
            raise ErroAutenticacao("O serviço recusou a credencial.")

        codigo, saida, erro = rodar(["--texto", "fato"], ENV_VALIDO, chamar=recusa)
        self.assertEqual(codigo, 3)
        self.assertIn("credencial", erro)
        self.assertNotIn(CHAVE_FALSA, saida + erro)
        self.assertNotIn("Traceback", erro)

    def test_falha_de_comunicacao(self):
        def falha(_s, _c):
            raise ErroComunicacao("Não foi possível se comunicar com o serviço.")

        codigo, _, erro = rodar(["--texto", "fato"], ENV_VALIDO, chamar=falha)
        self.assertEqual(codigo, 4)
        self.assertIn("comunicar", erro)

    def test_resposta_em_formato_inesperado(self):
        codigo, _, erro = rodar(["--texto", "fato"], ENV_VALIDO, chamar=lambda s, c: "sem json")
        self.assertEqual(codigo, 5)
        self.assertNotIn("Traceback", erro)

    def test_erro_inesperado_nao_vaza_detalhes(self):
        def explode(_s, _c):
            raise RuntimeError(f"detalhe interno {CHAVE_FALSA}")

        codigo, saida, erro = rodar(["--texto", "fato"], ENV_VALIDO, chamar=explode)
        self.assertEqual(codigo, 99)
        self.assertNotIn(CHAVE_FALSA, saida + erro)

    def test_leitura_por_arquivo(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("Fatura de energia de outubro, R$ 12.400,00.")
        try:
            codigo, saida, _ = rodar(["--arquivo", f.name], ENV_VALIDO,
                                     chamar=lambda s, c: RESPOSTA_JSON_OK)
        finally:
            os.unlink(f.name)
        self.assertEqual(codigo, 0)
        self.assertIn("Lançamento 1", saida)


class TestLogsSemDadosSensiveis(unittest.TestCase):
    def test_log_nao_contem_chave_nem_texto_do_fato(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = os.path.join(pasta, "execucao.log")
            env = {**ENV_VALIDO, "LOG_ARQUIVO": arquivo}
            rodar(["--texto", "FATO-CONFIDENCIAL-ABC"], env, chamar=lambda s, c: RESPOSTA_JSON_OK)
            with open(arquivo, encoding="utf-8") as f:
                conteudo = f.read()
        self.assertIn("execucao_ok", conteudo)
        self.assertNotIn(CHAVE_FALSA, conteudo)
        self.assertNotIn("FATO-CONFIDENCIAL-ABC", conteudo)


if __name__ == "__main__":
    unittest.main()
