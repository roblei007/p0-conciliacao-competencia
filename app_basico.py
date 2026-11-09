import os
import sys

from dotenv import load_dotenv
from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    InternalServerError,
    OpenAI,
    OpenAIError,
    PermissionDeniedError,
    RateLimitError,
)

SYSTEM_PROMPT = (
    "Transforme o fato operacional em lançamentos contábeis de partidas "
    "dobradas pelo regime de competência. Explique a competência."
)


class ConfigurationError(ValueError):
    pass


class InvalidResponseError(ValueError):
    pass


def _inteiro_positivo(nome: str, padrao: int) -> int:
    valor = os.getenv(nome, str(padrao)).strip()
    try:
        numero = int(valor)
    except ValueError as erro:
        raise ConfigurationError(f"A variável {nome} deve ser um inteiro positivo.") from erro
    if numero <= 0:
        raise ConfigurationError(f"A variável {nome} deve ser um inteiro positivo.")
    return numero


def consultar_llm(fato: str) -> str:
    url = os.getenv("LLM_API_URL", "").strip()
    modelo = os.getenv("LLM_MODEL", "").strip()
    chave = os.getenv("GROQ_API_KEY", "").strip()
    if not url:
        raise ConfigurationError("A variável LLM_API_URL não foi configurada.")
    if not modelo:
        raise ConfigurationError("A variável LLM_MODEL não foi configurada.")
    if not chave:
        raise ConfigurationError("A variável GROQ_API_KEY não foi configurada.")

    timeout = _inteiro_positivo("LLM_TIMEOUT", 120)
    max_tokens = _inteiro_positivo("LLM_MAX_TOKENS", 1000)
    cliente = OpenAI(
        base_url=url,
        api_key=chave,
        timeout=timeout,
    )
    resposta = cliente.chat.completions.create(
        model=modelo,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": fato},
        ],
        max_tokens=max_tokens,
    )
    if resposta.choices and resposta.choices[0].finish_reason == "length":
        raise InvalidResponseError(
            "A resposta foi truncada pelo limite de tokens; aumente LLM_MAX_TOKENS."
        )
    conteudo = resposta.choices[0].message.content if resposta.choices else None
    if not isinstance(conteudo, str) or not conteudo.strip():
        raise InvalidResponseError("A resposta da API não contém texto.")
    return conteudo.strip()


def _classificar_erro_api(erro: OpenAIError) -> tuple[int, str]:
    if isinstance(erro, (AuthenticationError, PermissionDeniedError)):
        return 3, "A Groq recusou a chave ou não autorizou o acesso ao modelo."
    if isinstance(erro, (APIConnectionError, RateLimitError, InternalServerError)):
        return 4, "Falha de conexão, limite de requisições ou indisponibilidade da Groq."
    if isinstance(erro, APIStatusError):
        if erro.status_code == 429 or erro.status_code >= 500:
            return 4, f"A Groq retornou HTTP {erro.status_code}; tente novamente mais tarde."
        return 2, f"A Groq rejeitou a solicitação (HTTP {erro.status_code}); confira modelo e configuração."
    return 99, "O SDK OpenAI retornou um erro inesperado."


def main() -> int:
    load_dotenv()
    try:
        fato = input("Descreva o fato operacional: ").strip()
    except EOFError:
        print("Erro: entrada encerrada antes de informar o fato operacional.", file=sys.stderr)
        return 1
    if not fato:
        print("Erro: descreva o fato operacional.", file=sys.stderr)
        return 1

    try:
        print(consultar_llm(fato))
    except OpenAIError as erro:
        codigo, mensagem = _classificar_erro_api(erro)
        print(f"Erro: {mensagem}", file=sys.stderr)
        return codigo
    except ConfigurationError as erro:
        print(f"Erro de configuração: {erro}", file=sys.stderr)
        return 2
    except InvalidResponseError as erro:
        print(f"Erro na resposta da LLM: {erro}", file=sys.stderr)
        return 5
    except ValueError as erro:
        print(f"Erro de configuração: {erro}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
