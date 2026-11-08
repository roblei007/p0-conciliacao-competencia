"""Interpretação e validação da resposta do modelo."""

import json
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import List

from .erros import ErroResposta

CAMPOS_TEXTO = ("conta_debito", "conta_credito", "historico", "justificativa_competencia")


@dataclass(frozen=True)
class Lancamento:
    data_competencia: date
    conta_debito: str
    conta_credito: str
    valor: Decimal
    historico: str
    justificativa_competencia: str


@dataclass(frozen=True)
class Resultado:
    lancamentos: List[Lancamento]
    alertas: List[str] = field(default_factory=list)


def extrair_json(texto: str) -> dict:
    """Converte o texto do modelo em dict, tolerando cercas ``` ou texto ao redor."""
    texto = (texto or "").strip()
    if not texto:
        raise ErroResposta("O modelo devolveu uma resposta vazia.")
    texto = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto, flags=re.IGNORECASE)
    try:
        dados = json.loads(texto)
    except json.JSONDecodeError:
        inicio, fim = texto.find("{"), texto.rfind("}")
        if inicio == -1 or fim <= inicio:
            raise ErroResposta("O modelo não devolveu JSON. Tente executar novamente.") from None
        try:
            dados = json.loads(texto[inicio : fim + 1])
        except json.JSONDecodeError:
            raise ErroResposta(
                "O JSON devolvido pelo modelo é inválido. Tente executar novamente."
            ) from None
    if not isinstance(dados, dict):
        raise ErroResposta("O modelo devolveu JSON em formato inesperado.")
    return dados


def _validar_lancamento(item, posicao: int) -> Lancamento:
    rotulo = f"lançamento {posicao}"
    if not isinstance(item, dict):
        raise ErroResposta(f"O {rotulo} devolvido pelo modelo está em formato inesperado.")

    for campo in CAMPOS_TEXTO:
        if not isinstance(item.get(campo), str) or not item[campo].strip():
            raise ErroResposta(f"O {rotulo} não tem o campo obrigatório '{campo}'.")

    try:
        data = date.fromisoformat(str(item.get("data_competencia")))
    except ValueError:
        raise ErroResposta(
            f"O {rotulo} tem data_competencia inválida (esperado AAAA-MM-DD)."
        ) from None

    bruto = item.get("valor")
    if isinstance(bruto, bool) or not isinstance(bruto, (int, float)):
        raise ErroResposta(f"O {rotulo} tem valor que não é numérico.")
    try:
        valor = Decimal(str(bruto)).quantize(Decimal("0.01"))
    except InvalidOperation:
        raise ErroResposta(f"O {rotulo} tem valor inválido.") from None
    if valor <= 0:
        raise ErroResposta(f"O {rotulo} tem valor menor ou igual a zero.")

    return Lancamento(
        data_competencia=data,
        conta_debito=item["conta_debito"].strip(),
        conta_credito=item["conta_credito"].strip(),
        valor=valor,
        historico=item["historico"].strip(),
        justificativa_competencia=item["justificativa_competencia"].strip(),
    )


def interpretar_resposta(texto: str) -> Resultado:
    """Valida o JSON do modelo e o converte em objetos tipados."""
    dados = extrair_json(texto)
    itens = dados.get("lancamentos")
    alertas = dados.get("alertas", [])

    if not isinstance(itens, list):
        raise ErroResposta("A resposta do modelo não contém a lista 'lancamentos'.")
    if not isinstance(alertas, list) or not all(isinstance(a, str) for a in alertas):
        raise ErroResposta("O campo 'alertas' da resposta está em formato inesperado.")

    lancamentos = [_validar_lancamento(item, i) for i, item in enumerate(itens, start=1)]
    if not lancamentos and not alertas:
        raise ErroResposta("O modelo não gerou lançamentos nem explicou o motivo.")
    return Resultado(lancamentos=lancamentos, alertas=[a.strip() for a in alertas if a.strip()])
