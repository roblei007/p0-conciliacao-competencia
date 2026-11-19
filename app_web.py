import os

from dotenv import load_dotenv
from flask import Flask, render_template, request
from openai import OpenAIError

from app_basico import (
    ConfigurationError,
    InvalidResponseError,
    classificar_erro_api,
    consultar_llm,
)

load_dotenv()

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index() -> str | tuple[str, int]:
    fato = ""
    resposta = None
    erro = None
    status = 200

    if request.method == "POST":
        fato = request.form.get("fato", "").strip()
        if not fato:
            erro = "Descreva o fato operacional."
            status = 400
        else:
            try:
                resposta = consultar_llm(fato)
            except ConfigurationError as excecao:
                erro = f"Erro de configuração: {excecao}"
                status = 500
            except InvalidResponseError as excecao:
                erro = f"Erro na resposta da LLM: {excecao}"
                status = 502
            except OpenAIError as excecao:
                codigo, mensagem = classificar_erro_api(excecao)
                erro = f"Erro no serviço LLM: {mensagem}"
                status = 503 if codigo == 4 else 502

    return render_template("index.html", fato=fato, resposta=resposta, erro=erro), status


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
