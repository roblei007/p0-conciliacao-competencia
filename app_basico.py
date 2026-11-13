import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

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


class LLMServiceError(Exception):
    def __init__(self, codigo: int, mensagem: str) -> None:
        super().__init__(mensagem)
        self.codigo = codigo


def _inteiro_positivo(nome: str, padrao: int) -> int:
    valor = os.getenv(nome, str(padrao)).strip()
    try:
        numero = int(valor)
    except ValueError as erro:
        raise ConfigurationError(f"A variável {nome} deve ser um inteiro positivo.") from erro
    if numero <= 0:
        raise ConfigurationError(f"A variável {nome} deve ser um inteiro positivo.")
    return numero


def _consultar_ollama(host: str, modelo: str, fato: str, timeout: int, max_tokens: int) -> str:
    requisicao = Request(
        url=f"{host.rstrip('/')}/api/chat",
        data=json.dumps(
            {
                "model": modelo,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": fato},
                ],
                "stream": False,
                "options": {"num_predict": max_tokens},
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(requisicao, timeout=timeout) as resposta:
            dados = json.loads(resposta.read())
    except HTTPError as erro:
        if erro.code in (401, 403):
            raise LLMServiceError(3, f"O Ollama recusou a solicitação (HTTP {erro.code}).") from erro
        if erro.code == 429 or erro.code >= 500:
            raise LLMServiceError(4, f"O Ollama retornou HTTP {erro.code}; tente novamente mais tarde.") from erro
        raise LLMServiceError(2, f"O Ollama rejeitou a solicitação (HTTP {erro.code}).") from erro
    except (URLError, TimeoutError) as erro:
        raise LLMServiceError(
            4, "Falha de conexão ou timeout com o Ollama; verifique host, rede e disponibilidade."
        ) from erro
    except (json.JSONDecodeError, UnicodeDecodeError) as erro:
        raise InvalidResponseError("A resposta do Ollama não contém JSON válido.") from erro

    if not isinstance(dados, dict):
        raise InvalidResponseError("A resposta do Ollama tem formato inválido.")
    if dados.get("error"):
        raise LLMServiceError(2, f"O Ollama rejeitou a solicitação: {dados['error']}")
    if dados.get("done_reason") == "length":
        raise InvalidResponseError(
            "A resposta foi truncada pelo limite de tokens; aumente LLM_MAX_TOKENS."
        )
    mensagem = dados.get("message")
    conteudo = mensagem.get("content") if isinstance(mensagem, dict) else None
    if not isinstance(conteudo, str) or not conteudo.strip():
        raise InvalidResponseError("A resposta do Ollama não contém texto.")
    return conteudo.strip()


def consultar_llm(fato: str) -> str:
    host_ollama = os.getenv("LLM_OLLAMA_HOST_URL", "").strip()
    url = os.getenv("LLM_API_URL", "").strip()
    modelo = os.getenv("LLM_MODEL", "").strip()
    chave = os.getenv("GROQ_API_KEY", "").strip()
    if not modelo:
        raise ConfigurationError("A variável LLM_MODEL não foi configurada.")

    timeout = _inteiro_positivo("LLM_TIMEOUT", 120)
    max_tokens = _inteiro_positivo("LLM_MAX_TOKENS", 1000)
    if host_ollama:
        return _consultar_ollama(host_ollama, modelo, fato, timeout, max_tokens)
    if not url:
        raise ConfigurationError("Configure LLM_OLLAMA_HOST_URL ou LLM_API_URL.")
    if not chave:
        raise ConfigurationError("A variável GROQ_API_KEY é obrigatória para LLM_API_URL.")

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
        return 3, "O serviço LLM recusou a chave ou não autorizou o acesso ao modelo."
    if isinstance(erro, (APIConnectionError, RateLimitError, InternalServerError)):
        return 4, "Falha de conexão, limite de requisições ou indisponibilidade do serviço LLM."
    if isinstance(erro, APIStatusError):
        if erro.status_code == 429 or erro.status_code >= 500:
            return 4, f"O serviço LLM retornou HTTP {erro.status_code}; tente novamente mais tarde."
        return 2, f"O serviço LLM rejeitou a solicitação (HTTP {erro.status_code}); confira modelo e configuração."
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
    except LLMServiceError as erro:
        print(f"Erro no serviço LLM: {erro}", file=sys.stderr)
        return erro.codigo
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
