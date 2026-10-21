FROM python:3.12-slim

WORKDIR /app
COPY server.py ./
COPY 0*.html instructor-activity-guide.html ./

USER nobody
ENV PYTHONUNBUFFERED=1
CMD ["python", "server.py"]
