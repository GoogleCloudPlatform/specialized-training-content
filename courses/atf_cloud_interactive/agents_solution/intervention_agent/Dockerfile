FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

EXPOSE 8080
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN uv pip install --no-cache --system -r requirements.txt

COPY . ./

ENTRYPOINT ["sh", "-c", "uvicorn agent:a2a_app --host 0.0.0.0 --port ${PORT:-8080}"]
