"""Chamada ao LLM por API REST (Messages API) e classificação de falhas."""

import logging
import time

import requests

from .config import Configuracao
from .erros import (
    ErroAutenticacao,
    ErroComunicacao,
    ErroResposta,
    ErroServicoIndisponivel,
)

log = logging.getLogger("lancamentos")


def _cabecalhos(config: Configuracao) -> dict:
    if config.formato == "openai":
        return {
            "Authorization": f"Bearer {config.api_key}",
            "content-type": "application/json",
        }
    return {
        "x-api-key": config.api_key,
        "anthropic-version": config.api_version,
        "content-type": "application/json",
    }


def _mensagem_api(resposta) -> str:
    """Extrai a mensagem de erro devolvida pelo serviço, se houver."""
    try:
        return str(resposta.json()["error"]["message"])[:200]
    except Exception:
        return ""


_MSG_TRUNCADA = (
    "A resposta foi cortada por atingir o limite de tokens. "
    "Aumente LLM_MAX_TOKENS no arquivo .env ou reduza o fato descrito."
)


def extrair_texto(dados, formato: str = "anthropic") -> str:
    """Obtém o texto do corpo JSON da resposta; falha se vazio, truncado ou inesperado."""
    if formato == "openai":
        texto = _texto_openai(dados)
    else:
        texto = _texto_anthropic(dados)
    if not texto:
        raise ErroResposta("O serviço devolveu uma resposta vazia.")
    return texto


def _texto_anthropic(dados) -> str:
    if not isinstance(dados, dict) or not isinstance(dados.get("content"), list):
        raise ErroResposta("O serviço devolveu uma resposta em formato inesperado.")
    if dados.get("stop_reason") == "max_tokens":
        raise ErroResposta(_MSG_TRUNCADA)
    partes = [
        bloco.get("text", "")
        for bloco in dados["content"]
        if isinstance(bloco, dict) and bloco.get("type") == "text"
    ]
    return "".join(partes).strip()


def _texto_openai(dados) -> str:
    try:
        escolha = dados["choices"][0]
        conteudo = escolha["message"]["content"]
    except (TypeError, KeyError, IndexError):
        raise ErroResposta("O serviço devolveu uma resposta em formato inesperado.") from None
    if escolha.get("finish_reason") == "length":
        raise ErroResposta(_MSG_TRUNCADA)
    return conteudo.strip() if isinstance(conteudo, str) else ""


def chamar_llm(solicitacao: dict, config: Configuracao) -> str:
    """Envia a solicitação e devolve o texto da resposta do modelo."""
    inicio = time.monotonic()
    try:
        resposta = requests.post(
            config.api_url,
            headers=_cabecalhos(config),
            json=solicitacao,
            timeout=config.timeout,
        )
    except requests.exceptions.Timeout:
        log.warning("chamada_llm resultado=timeout limite_s=%s", config.timeout)
        raise ErroComunicacao(
            f"O serviço não respondeu em {config.timeout:g} segundos. "
            "Tente novamente ou aumente LLM_TIMEOUT."
        ) from None
    except requests.exceptions.RequestException as exc:
        log.warning("chamada_llm resultado=falha_rede tipo=%s", type(exc).__name__)
        raise ErroComunicacao(
            "Não foi possível se comunicar com o serviço. Verifique sua conexão com a "
            "internet e o endereço LLM_API_URL."
        ) from None

    duracao_ms = int((time.monotonic() - inicio) * 1000)
    status = resposta.status_code
    log.info("chamada_llm modelo=%s status=%s duracao_ms=%s", config.modelo, status, duracao_ms)

    if status == 401:
        raise ErroAutenticacao(
            "O serviço recusou a credencial (erro de autenticação). Verifique se "
            "LLM_API_KEY está correta e ativa."
        )
    if status == 403:
        raise ErroAutenticacao(
            "Acesso negado pelo serviço (HTTP 403). A chave pode não ter permissão para "
            "este modelo ou o acesso pode estar bloqueado por proxy/firewall da rede."
        )
    if status == 429 or status >= 500:
        raise ErroServicoIndisponivel(
            f"O serviço está indisponível ou sobrecarregado no momento (HTTP {status}). "
            "Aguarde alguns instantes e tente novamente."
        )
    if status >= 400:
        detalhe = _mensagem_api(resposta)
        raise ErroComunicacao(
            f"O serviço rejeitou a solicitação (HTTP {status})."
            + (f" Detalhe: {detalhe}" if detalhe else "")
            + " Verifique LLM_MODEL e os demais parâmetros."
        )

    try:
        dados = resposta.json()
    except ValueError:
        raise ErroResposta("O serviço devolveu algo que não é JSON válido.") from None
    return extrair_texto(dados, config.formato)
