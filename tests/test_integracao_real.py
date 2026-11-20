"""Testes COM chamada real ao serviço. Ignorados por padrão.

Para executar:  RUN_REAL_TESTS=1 python -m unittest tests.test_integracao_real -v
(Linux/macOS)   No PowerShell: $env:RUN_REAL_TESTS="1"
Exigem internet e, no primeiro teste, uma LLM_API_KEY válida no .env (consome créditos).
"""

import os
import unittest
from dataclasses import replace

from lancamentos.cliente_llm import chamar_llm
from lancamentos.config import carregar_configuracao
from lancamentos.erros import ErroAutenticacao
from lancamentos.prompt import preparar_solicitacao
from lancamentos.resposta import interpretar_resposta

EXECUTAR = os.getenv("RUN_REAL_TESTS") == "1"
FATO = (
    "Em 28/10/2026 o banco recebeu a fatura de energia elétrica da agência central, "
    "no valor de R$ 12.400,00, referente ao consumo de 01/10/2026 a 31/10/2026, "
    "com vencimento em 10/11/2026."
)


@unittest.skipUnless(EXECUTAR, "defina RUN_REAL_TESTS=1 para executar chamadas reais")
class TestIntegracaoReal(unittest.TestCase):
    def test_entrada_valida_gera_lancamento_de_competencia(self):
        config = carregar_configuracao()
        texto = chamar_llm(preparar_solicitacao(FATO, config), config)
        resultado = interpretar_resposta(texto)
        self.assertGreaterEqual(len(resultado.lancamentos), 1)
        self.assertEqual(resultado.lancamentos[0].data_competencia.month, 10)

    def test_credencial_invalida_real(self):
        config = replace(carregar_configuracao(), api_key="chave-invalida-de-proposito")
        with self.assertRaises(ErroAutenticacao):
            chamar_llm(preparar_solicitacao(FATO, config), config)


if __name__ == "__main__":
    unittest.main()
