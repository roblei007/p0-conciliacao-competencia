import json
import unittest
from datetime import date
from decimal import Decimal

from lancamentos.apresentacao import formatar_resultado, formatar_valor
from lancamentos.erros import ErroResposta
from lancamentos.resposta import interpretar_resposta
from tests.auxiliares import LANCAMENTO_OK, RESPOSTA_JSON_OK


def com(**alteracoes):
    item = {**LANCAMENTO_OK, **alteracoes}
    return json.dumps({"lancamentos": [item], "alertas": []})


class TestInterpretarResposta(unittest.TestCase):
    def test_resposta_valida(self):
        r = interpretar_resposta(RESPOSTA_JSON_OK)
        self.assertEqual(len(r.lancamentos), 1)
        lanc = r.lancamentos[0]
        self.assertEqual(lanc.valor, Decimal("12400.00"))
        self.assertEqual(lanc.data_competencia, date(2026, 10, 31))

    def test_tolera_cerca_de_codigo_e_texto_ao_redor(self):
        self.assertEqual(len(interpretar_resposta(f"```json\n{RESPOSTA_JSON_OK}\n```").lancamentos), 1)
        self.assertEqual(len(interpretar_resposta(f"Aqui está:\n{RESPOSTA_JSON_OK}\nFim.").lancamentos), 1)

    def test_sem_lancamentos_mas_com_alerta_e_aceito(self):
        texto = json.dumps({"lancamentos": [], "alertas": ["Valor não informado."]})
        r = interpretar_resposta(texto)
        self.assertEqual(r.lancamentos, [])
        self.assertEqual(r.alertas, ["Valor não informado."])

    def test_respostas_invalidas(self):
        casos = {
            "vazia": "",
            "sem json": "não consegui processar",
            "json quebrado": '{"lancamentos": [',
            "lista na raiz": "[1, 2]",
            "sem chave lancamentos": '{"alertas": []}',
            "lancamentos vazio sem alerta": '{"lancamentos": [], "alertas": []}',
            "alertas mal formatados": '{"lancamentos": [], "alertas": "x"}',
            "data inválida": com(data_competencia="31/10/2026"),
            "data impossível": com(data_competencia="2026-02-30"),
            "valor texto": com(valor="12.400,00"),
            "valor zero": com(valor=0),
            "valor negativo": com(valor=-5),
            "valor booleano": com(valor=True),
            "conta vazia": com(conta_debito="  "),
            "campo ausente": json.dumps(
                {"lancamentos": [{k: v for k, v in LANCAMENTO_OK.items() if k != "historico"}]}
            ),
        }
        for nome, texto in casos.items():
            with self.subTest(caso=nome):
                with self.assertRaises(ErroResposta):
                    interpretar_resposta(texto)


class TestApresentacao(unittest.TestCase):
    def test_formatar_valor_padrao_brasileiro(self):
        self.assertEqual(formatar_valor(Decimal("1234.5")), "R$ 1.234,50")
        self.assertEqual(formatar_valor(Decimal("12400")), "R$ 12.400,00")
        self.assertEqual(formatar_valor(Decimal("0.99")), "R$ 0,99")

    def test_saida_contem_partidas_e_aviso(self):
        saida = formatar_resultado(interpretar_resposta(RESPOSTA_JSON_OK))
        self.assertIn("31/10/2026", saida)
        self.assertIn("Despesa com energia elétrica", saida)
        self.assertIn("R$ 12.400,00", saida)
        self.assertIn("revise", saida)


if __name__ == "__main__":
    unittest.main()
