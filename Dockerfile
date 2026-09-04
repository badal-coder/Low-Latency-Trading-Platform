FROM python:3.13-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir prometheus-client

EXPOSE 8000

CMD ["python", "-m", "engine.metrics_server", "--host", "0.0.0.0", "--port", "8000"]