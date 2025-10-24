FROM python:3.11-slim

WORKDIR /app

RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app

USER appuser

COPY --chown=appuser:appuser requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appuser src/ ./src/

RUN mkdir -p /app/data

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/stats')" || exit 1

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]
