"""Erros previsíveis da aplicação.

Cada erro carrega uma mensagem compreensível para o usuário e um código de
saída do processo, para que o terminal (ou um script) saiba o que ocorreu.
"""


class ErroAplicacao(Exception):
    codigo_saida = 99


class ErroEntrada(ErroAplicacao):
    """Entrada vazia, grande demais ou ilegível."""

    codigo_saida = 1


class ErroConfiguracao(ErroAplicacao):
    """Configuração de acesso ausente ou inválida."""

    codigo_saida = 2


class ErroCredencialAusente(ErroConfiguracao):
    """A chave de acesso ao LLM não foi informada."""


class ErroAutenticacao(ErroAplicacao):
    """O serviço recusou a credencial (HTTP 401/403)."""

    codigo_saida = 3


class ErroServicoIndisponivel(ErroAplicacao):
    """O serviço está fora do ar, sobrecarregado ou limitando requisições."""

    codigo_saida = 4


class ErroComunicacao(ErroAplicacao):
    """Falha de rede, timeout ou requisição rejeitada."""

    codigo_saida = 4


class ErroResposta(ErroAplicacao):
    """Resposta vazia, truncada ou em formato inesperado."""

    codigo_saida = 5
