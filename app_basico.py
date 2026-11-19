import os
import socket

from openai import (
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    DefaultHttpxClient,
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
    base_url = (
        os.getenv("LLM_BASE_URL", "https://llm-internal.softex:9001/v1").strip()
        or "https://llm-internal.softex:9001/v1"
    )
    modelo = os.getenv("LLM_MODEL", "qwen3.5:9b-q4_K_M").strip() or "qwen3.5:9b-q4_K_M"
    chave = os.getenv("LLM_API_KEY", "qualquer").strip() or "qualquer"

    timeout = _inteiro_positivo("LLM_TIMEOUT", 120)
    max_tokens = _inteiro_positivo("LLM_MAX_TOKENS", 2000)

    with OpenAI(
        base_url=base_url,
        api_key=chave,
        timeout=timeout,
        http_client=DefaultHttpxClient(verify=False),
    ) as cliente:
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


def classificar_erro_api(erro: OpenAIError) -> tuple[int, str]:
    if isinstance(erro, (AuthenticationError, PermissionDeniedError)):
        return 3, "O serviço LLM recusou a chave ou não autorizou o acesso ao modelo."
    if isinstance(erro, APIConnectionError):
        causa = erro.__cause__
        while causa is not None:
            if isinstance(causa, socket.gaierror):
                return 4, (
                    "Não foi possível resolver o endereço da LLM; verifique o DNS "
                    "e o acesso à rede interna (llm-internal.softex)."
                )
            causa = causa.__cause__ or causa.__context__
        return 4, "Falha de conexão, limite de requisições ou indisponibilidade do serviço LLM."
    if isinstance(erro, (RateLimitError, InternalServerError)):
        return 4, "Falha de conexão, limite de requisições ou indisponibilidade do serviço LLM."
    if isinstance(erro, APIStatusError):
        if erro.status_code == 429 or erro.status_code >= 500:
            return 4, f"O serviço LLM retornou HTTP {erro.status_code}; tente novamente mais tarde."
        return 2, f"O serviço LLM rejeitou a solicitação (HTTP {erro.status_code}); confira modelo e configuração."
    return 99, "O SDK OpenAI retornou um erro inesperado."
