FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LLM_BASE_URL=https://llm-internal.softex:9001/v1 \
    LLM_MODEL=qwen3.5:9b-q4_K_M \
    PORT=8000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --uid 10001 appuser
COPY --chown=appuser:appuser app_basico.py app_web.py ./
COPY --chown=appuser:appuser templates/ ./templates/
USER appuser

EXPOSE 8000

CMD ["sh", "-c", "exec waitress-serve --listen=0.0.0.0:${PORT:-8000} app_web:app"]
