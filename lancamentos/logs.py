"""Registros simples de execução.

Política: nunca registrar chaves, o texto do fato operacional nem o conteúdo
da resposta. Apenas metadados (modelo, status, duração, tamanhos, contagens).
"""

import logging
import os

from .config import Configuracao

NOME_LOGGER = "lancamentos"


def configurar_logs(config: Configuracao) -> logging.Logger:
    logger = logging.getLogger(NOME_LOGGER)
    logger.setLevel(config.log_nivel)

    for antigo in [h for h in logger.handlers if getattr(h, "_lancamentos", False)]:
        logger.removeHandler(antigo)
        antigo.close()

    try:
        pasta = os.path.dirname(config.log_arquivo)
        if pasta:
            os.makedirs(pasta, exist_ok=True)
        handler = logging.FileHandler(config.log_arquivo, encoding="utf-8")
    except OSError:
        handler = logging.NullHandler()  # sem permissão de escrita: segue sem log
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    handler._lancamentos = True
    logger.addHandler(handler)
    return logger
