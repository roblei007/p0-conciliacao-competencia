"""Dados e utilitários compartilhados pelos testes (nenhum acessa a rede)."""

import json
from unittest.mock import MagicMock

from lancamentos.config import Configuracao

CHAVE_FALSA = "chave-falsa-SEGREDO-123"

CONFIG = Configuracao(api_key=CHAVE_FALSA, modelo="modelo-teste", log_arquivo="")

LANCAMENTO_OK = {
    "data_competencia": "2026-10-31",
    "conta_debito": "Despesa com energia elétrica",
    "conta_credito": "Energia elétrica a pagar",
    "valor": 12400.00,
    "historico": "Consumo de energia da agência central - outubro/2026",
    "justificativa_competencia": "Consumo ocorreu em outubro, independentemente do vencimento.",
}

RESPOSTA_JSON_OK = json.dumps({"lancamentos": [LANCAMENTO_OK], "alertas": []})


def resposta_http(status=200, corpo=None, json_invalido=False):
    """Simula um objeto requests.Response."""
    resp = MagicMock()
    resp.status_code = status
    if json_invalido:
        resp.json.side_effect = ValueError("sem json")
    else:
        resp.json.return_value = corpo if corpo is not None else {}
    return resp


def corpo_texto(texto, stop_reason="end_turn"):
    return {"content": [{"type": "text", "text": texto}], "stop_reason": stop_reason}
