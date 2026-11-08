"""Carregamento e validação da configuração (variáveis de ambiente / .env)."""

import os
from dataclasses import dataclass, field
from typing import Mapping, Optional

from dotenv import load_dotenv

from .erros import ErroConfiguracao, ErroCredencialAusente

URL_PADRAO = "https://api.anthropic.com/v1/messages"
VERSAO_API_PADRAO = "2023-06-01"


@dataclass(frozen=True)
class Configuracao:
    # repr=False: a chave nunca aparece em print(), logs ou tracebacks.
    api_key: str = field(repr=False)
    modelo: str
    api_url: str = URL_PADRAO
    api_version: str = VERSAO_API_PADRAO
    max_tokens: int = 1500
    temperatura: Optional[float] = 0.0
    timeout: float = 30.0
    log_nivel: str = "INFO"
    log_arquivo: str = "logs/execucao.log"
    formato: str = "anthropic"  # "anthropic" (Messages API) ou "openai" (chat/completions)


FORMATOS = ("anthropic", "openai")


def _numero(env: Mapping[str, str], nome: str, tipo, padrao, minimo, maximo=None):
    bruto = (env.get(nome) or "").strip()
    if not bruto:
        return padrao
    try:
        valor = tipo(bruto)
    except ValueError:
        raise ErroConfiguracao(
            f"A variável {nome} tem o valor '{bruto}', que não é um número válido."
        ) from None
    if valor < minimo or (maximo is not None and valor > maximo):
        faixa = f"entre {minimo} e {maximo}" if maximo is not None else f">= {minimo}"
        raise ErroConfiguracao(f"A variável {nome} deve estar {faixa} (valor atual: {valor}).")
    return valor


def carregar_configuracao(env: Optional[Mapping[str, str]] = None) -> Configuracao:
    """Lê a configuração. Se `env` não for informado, usa o ambiente + arquivo .env."""
    if env is None:
        load_dotenv()
        env = os.environ

    chave = (env.get("LLM_API_KEY") or "").strip()
    if not chave:
        raise ErroCredencialAusente(
            "A variável LLM_API_KEY não foi encontrada. Copie .env.example para .env "
            "e preencha a chave de acesso (consulte o README)."
        )

    modelo = (env.get("LLM_MODEL") or "").strip()
    if not modelo:
        raise ErroConfiguracao(
            "A variável LLM_MODEL não foi informada. Defina o nome do modelo no arquivo .env."
        )

    formato = (env.get("LLM_API_FORMAT") or "anthropic").strip().lower()
    if formato not in FORMATOS:
        raise ErroConfiguracao("LLM_API_FORMAT deve ser 'anthropic' ou 'openai'.")

    url = (env.get("LLM_API_URL") or "").strip()
    if not url:
        if formato == "openai":
            raise ErroConfiguracao(
                "Com LLM_API_FORMAT=openai, informe LLM_API_URL (endereço completo do "
                "endpoint de chat/completions do seu provedor)."
            )
        url = URL_PADRAO
    if not (url.startswith("https://") or url.startswith("http://localhost")):
        raise ErroConfiguracao("LLM_API_URL deve começar com https:// (ou http://localhost).")

    nivel = (env.get("LOG_LEVEL") or "INFO").strip().upper()
    if nivel not in {"DEBUG", "INFO", "WARNING", "ERROR"}:
        raise ErroConfiguracao("LOG_LEVEL deve ser DEBUG, INFO, WARNING ou ERROR.")

    return Configuracao(
        api_key=chave,
        modelo=modelo,
        api_url=url,
        api_version=(env.get("LLM_API_VERSION") or VERSAO_API_PADRAO).strip(),
        max_tokens=_numero(env, "LLM_MAX_TOKENS", int, 1500, 1, 8192),
        temperatura=_numero(env, "LLM_TEMPERATURE", float, 0.0, 0.0, 1.0),
        timeout=_numero(env, "LLM_TIMEOUT", float, 30.0, 1.0, 300.0),
        log_nivel=nivel,
        log_arquivo=(env.get("LOG_ARQUIVO") or "logs/execucao.log").strip(),
        formato=formato,
    )
