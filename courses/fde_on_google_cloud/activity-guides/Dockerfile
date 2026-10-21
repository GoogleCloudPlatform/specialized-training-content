FROM python:3.12-slim

RUN python3 -m pip install --no-cache-dir --upgrade pip \
 && python3 -m pip install --no-cache-dir --upgrade "certifi>=2026.10.19"

WORKDIR /app
COPY server.py ./
COPY html/ ./html/

USER nobody
ENV PYTHONUNBUFFERED=1
CMD ["python", "server.py"]
