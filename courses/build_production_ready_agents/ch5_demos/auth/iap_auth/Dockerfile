FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY main.py /app/main.py

RUN pip install --no-cache-dir Flask

EXPOSE 8080

CMD ["python", "main.py"]
