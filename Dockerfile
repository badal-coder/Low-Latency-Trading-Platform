FROM python:3.13-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir fastapi uvicorn passlib[bcrypt] PyJWT prometheus-client

EXPOSE 8000

CMD ["uvicorn", "engine.api:app", "--host", "0.0.0.0", "--port", "8000"]
