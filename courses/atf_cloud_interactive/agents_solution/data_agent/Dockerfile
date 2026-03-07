FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

EXPOSE 8080
WORKDIR /app

COPY requirements.txt ./
RUN uv pip install --no-cache --system -r requirements.txt

COPY . ./

ENTRYPOINT ["sh", "-c", "uvicorn agent:a2a_app --host 0.0.0.0 --port ${PORT:-8080}"]