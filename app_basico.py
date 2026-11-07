import os

import requests
from dotenv import load_dotenv

load_dotenv()
chave = os.environ["LLM_API_KEY"]
modelo = os.environ["LLM_MODEL"]

fato = input("Descreva o fato operacional: ")

resposta = requests.post(
    "https://api.anthropic.com/v1/messages",
    headers={
        "x-api-key": chave,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    },
    json={
        "model": modelo,
        "max_tokens": 1000,
        "system": "Transforme o fato operacional em lançamentos contábeis de partidas "
                  "dobradas pelo regime de competência. Explique a competência.",
        "messages": [{"role": "user", "content": fato}],
    },
    timeout=30,
)
print(resposta.json()["content"][0]["text"])