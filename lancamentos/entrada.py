"""Captura e validação da entrada textual."""

import sys
from typing import Callable

from .erros import ErroEntrada

LIMITE_CARACTERES = 4000


def validar_entrada(texto) -> str:
    """Impede o envio de entradas vazias ou grandes demais ao LLM."""
    if texto is None or not str(texto).strip():
        raise ErroEntrada(
            "Entrada vazia. Descreva o fato operacional (o que ocorreu, quando, valor e período)."
        )
    texto = str(texto).strip()
    if len(texto) > LIMITE_CARACTERES:
        raise ErroEntrada(
            f"Entrada com {len(texto)} caracteres; o limite é {LIMITE_CARACTERES}. "
            "Divida em fatos menores."
        )
    return texto


def capturar_entrada_terminal(ler_linha: Callable[[str], str] = input) -> str:
    """Lê linhas do terminal até uma linha vazia (ou fim da entrada)."""
    print(
        "Descreva o fato operacional. Termine com uma linha vazia:",
        file=sys.stderr,
    )
    linhas = []
    while True:
        try:
            linha = ler_linha("> ")
        except EOFError:
            break
        if not linha.strip():
            break
        linhas.append(linha)
    return "\n".join(linhas)


def ler_arquivo(caminho: str) -> str:
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            return arquivo.read()
    except FileNotFoundError:
        raise ErroEntrada(f"Arquivo não encontrado: {caminho}") from None
    except (OSError, UnicodeDecodeError):
        raise ErroEntrada(f"Não foi possível ler o arquivo '{caminho}' como texto UTF-8.") from None
