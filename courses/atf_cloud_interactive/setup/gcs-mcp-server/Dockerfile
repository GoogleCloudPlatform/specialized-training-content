# GCS MCP Server — Cloud Run deployment
#
# Custom Python FastMCP server wrapping google-cloud-storage.
# Exposes list_objects, read_object, and write_object tools over
# Streamable HTTP at /mcp.

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

CMD ["python", "server.py"]
