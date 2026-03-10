FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml poetry.lock* ./
RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction

COPY shared ./shared
COPY producer ./producer
COPY consumer ./consumer
COPY alembic.ini ./

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["uvicorn", "producer.main:app", "--host", "0.0.0.0", "--port", "8000"]
