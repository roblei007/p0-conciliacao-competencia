import unittest
from dataclasses import replace

from lancamentos.prompt import PROMPT_SISTEMA, preparar_solicitacao
from tests.auxiliares import CONFIG


class TestPrepararSolicitacao(unittest.TestCase):
    def test_estrutura_da_solicitacao(self):
        s = preparar_solicitacao("fatura de energia", CONFIG)
        self.assertEqual(s["model"], "modelo-teste")
        self.assertEqual(s["max_tokens"], CONFIG.max_tokens)
        self.assertEqual(s["system"], PROMPT_SISTEMA)
        conteudo = s["messages"][0]["content"]
        self.assertIn("<fato_operacional>\nfatura de energia\n</fato_operacional>", conteudo)

    def test_prompt_exige_competencia_e_json(self):
        self.assertIn("COMPETÊNCIA", PROMPT_SISTEMA)
        self.assertIn("JSON", PROMPT_SISTEMA)

    def test_temperatura_opcional(self):
        self.assertEqual(preparar_solicitacao("x", CONFIG)["temperature"], 0.0)
        sem_temp = replace(CONFIG, temperatura=None)
        self.assertNotIn("temperature", preparar_solicitacao("x", sem_temp))

    def test_formato_openai_usa_mensagem_de_sistema(self):
        cfg = replace(CONFIG, formato="openai")
        s = preparar_solicitacao("fato", cfg)
        self.assertNotIn("system", s)
        self.assertEqual([m["role"] for m in s["messages"]], ["system", "user"])
        self.assertEqual(s["messages"][0]["content"], PROMPT_SISTEMA)

    def test_chave_nao_vai_no_corpo(self):
        s = preparar_solicitacao("x", CONFIG)
        self.assertNotIn(CONFIG.api_key, str(s))


if __name__ == "__main__":
    unittest.main()
