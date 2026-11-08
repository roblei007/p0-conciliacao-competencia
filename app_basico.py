import os
import sys

import requests
from dotenv import load_dotenv

SYSTEM_PROMPT = (
    "Transforme o fato operacional em lançamentos contábeis de partidas "
    "dobradas pelo regime de competência. Explique a competência."
)


def consultar_llm(fato: str) -> str:
    url = os.getenv("LLM_API_URL", "").strip()
    modelo = os.getenv("LLM_MODEL", "").strip()
    if not url:
        raise ValueError("A variável LLM_API_URL não foi configurada.")
    if not modelo:
        raise ValueError("A variável LLM_MODEL não foi configurada.")

    cabecalhos = {"Content-Type": "application/json"}
    chave = os.getenv("LLM_API_KEY", "").strip()
    if chave:
        cabecalhos["Authorization"] = f"Bearer {chave}"

    resposta = requests.post(
        url,
        headers=cabecalhos,
        json={
            "model": modelo,
            "stream": False,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": fato},
            ],
            "options": {"num_predict": int(os.getenv("LLM_MAX_TOKENS", "1000"))},
        },
        timeout=int(os.getenv("LLM_TIMEOUT", "120")),
    )
    resposta.raise_for_status()

    try:
        dados = resposta.json()
    except ValueError as erro:
        raise ValueError("O servidor Ollama retornou uma resposta que não é JSON.") from erro

    mensagem = dados.get("message") if isinstance(dados, dict) else None
    conteudo = mensagem.get("content") if isinstance(mensagem, dict) else None
    if not isinstance(conteudo, str) or not conteudo.strip():
        raise ValueError("A resposta do Ollama não contém texto em message.content.")
    return conteudo.strip()


def main() -> int:
    load_dotenv()
    fato = input("Descreva o fato operacional: ").strip()
    if not fato:
        print("Erro: descreva o fato operacional.", file=sys.stderr)
        return 1

    try:
        print(consultar_llm(fato))
    except requests.exceptions.RequestException as erro:
        print(f"Erro ao acessar a LLM interna: {erro}", file=sys.stderr)
        return 2
    except ValueError as erro:
        print(f"Erro de configuração ou resposta da LLM: {erro}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
