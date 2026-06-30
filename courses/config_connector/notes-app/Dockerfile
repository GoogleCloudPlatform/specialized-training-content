# Lightweight Python base; slim keeps the image small for fast Cloud Run cold starts.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

WORKDIR /app

# Install dependencies first so this layer is cached across code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as a non-root user.
RUN useradd --create-home appuser
USER appuser

EXPOSE 8080

# gunicorn serves the Flask `app` object from app.py. Cloud Run injects $PORT.
# A single worker with a few threads is plenty for a single-student notes app.
# JSON-array form (no implicit shell) keeps signal handling clean; we invoke
# sh -c ourselves so ${PORT} still expands at runtime.
CMD ["sh", "-c", "exec gunicorn --bind \":${PORT}\" --workers 1 --threads 8 --timeout 0 app:app"]
