FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LLM_OLLAMA_HOST_URL=https://llm-internal.softex:9001 \
    LLM_MODEL=qwen3.5:9b-q4_K_M

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --uid 10001 appuser
COPY --chown=appuser:appuser app_basico.py .
USER appuser

ENTRYPOINT ["python", "app_basico.py"]
