"""Formatação do resultado para exibição no terminal."""

from decimal import Decimal

from .resposta import Resultado


def formatar_valor(valor: Decimal) -> str:
    """1234.5 -> 'R$ 1.234,50'."""
    inteiro = f"{valor:,.2f}"  # 1,234.50
    return "R$ " + inteiro.replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_resultado(resultado: Resultado) -> str:
    linhas = []
    for i, lanc in enumerate(resultado.lancamentos, start=1):
        valor = formatar_valor(lanc.valor)
        linhas += [
            f"Lançamento {i} | competência {lanc.data_competencia.strftime('%d/%m/%Y')}",
            f"  D  {lanc.conta_debito:<45} {valor:>16}",
            f"  C  {lanc.conta_credito:<45} {valor:>16}",
            f"  Histórico:   {lanc.historico}",
            f"  Competência: {lanc.justificativa_competencia}",
            "",
        ]
    if resultado.alertas:
        linhas.append("Pontos de atenção para o contador:")
        linhas += [f"  - {alerta}" for alerta in resultado.alertas]
        linhas.append("")
    linhas.append(
        "Sugestão gerada por IA: revise contas, valores e datas antes de contabilizar."
    )
    return "\n".join(linhas)
