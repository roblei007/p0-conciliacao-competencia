import io
import unittest
from contextlib import redirect_stderr

from lancamentos.entrada import (
    LIMITE_CARACTERES,
    capturar_entrada_terminal,
    ler_arquivo,
    validar_entrada,
)
from lancamentos.erros import ErroEntrada


class TestValidarEntrada(unittest.TestCase):
    def test_entrada_valida_remove_espacos(self):
        self.assertEqual(validar_entrada("  fato  \n"), "fato")

    def test_entrada_vazia_e_impedida(self):
        for vazia in ("", "   ", "\n\t", None):
            with self.subTest(entrada=vazia):
                with self.assertRaises(ErroEntrada) as ctx:
                    validar_entrada(vazia)
                self.assertIn("Entrada vazia", str(ctx.exception))

    def test_entrada_grande_demais(self):
        with self.assertRaises(ErroEntrada):
            validar_entrada("a" * (LIMITE_CARACTERES + 1))


class TestCapturaTerminal(unittest.TestCase):
    def test_le_varias_linhas_ate_linha_vazia(self):
        linhas = iter(["linha 1", "linha 2", "", "ignorada"])
        with redirect_stderr(io.StringIO()):
            texto = capturar_entrada_terminal(lambda _prompt: next(linhas))
        self.assertEqual(texto, "linha 1\nlinha 2")

    def test_fim_de_entrada_encerra_leitura(self):
        def ler(_prompt):
            raise EOFError

        with redirect_stderr(io.StringIO()):
            self.assertEqual(capturar_entrada_terminal(ler), "")


class TestLerArquivo(unittest.TestCase):
    def test_arquivo_inexistente(self):
        with self.assertRaises(ErroEntrada):
            ler_arquivo("nao_existe.txt")


if __name__ == "__main__":
    unittest.main()
