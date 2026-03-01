"""GCS MCP Server — Cloud Run deployment.

A lightweight MCP server that exposes Google Cloud Storage operations
as tools over Streamable HTTP. Deployed to Cloud Run, called by the
Intervention Agent to write intervention PDFs and read/list objects.

Endpoint: /mcp (Streamable HTTP transport)
"""

import base64
import os

import uvicorn
from fastmcp import FastMCP
from google.cloud import storage
from starlette.middleware.cors import CORSMiddleware

mcp = FastMCP("GCS Storage")

client = storage.Client()


@mcp.tool
def list_objects(bucket_name: str, prefix: str = "") -> dict:
    """List objects in a GCS bucket, optionally filtered by prefix.

    Args:
        bucket_name: The GCS bucket name (without gs:// prefix).
        prefix: Only return objects whose names begin with this prefix.
                Use 'customer_id/' to list a specific customer's files.
    """
    blobs = client.list_blobs(bucket_name, prefix=prefix)
    objects = [
        {"name": b.name, "size": b.size, "content_type": b.content_type}
        for b in blobs
    ]
    return {"bucket": bucket_name, "prefix": prefix, "count": len(objects), "objects": objects}


@mcp.tool
def read_object(bucket_name: str, object_name: str) -> dict:
    """Read the content of a GCS object as text.

    Args:
        bucket_name: The GCS bucket name (without gs:// prefix).
        object_name: Full object path within the bucket (e.g. 'customer_123/report.pdf').
    """
    blob = client.bucket(bucket_name).blob(object_name)
    content = blob.download_as_text()
    return {
        "bucket": bucket_name,
        "object": object_name,
        "content_type": blob.content_type,
        "size": blob.size,
        "content": content,
    }


@mcp.tool
def write_object(
    bucket_name: str,
    object_name: str,
    content: str,
    content_type: str = "text/plain",
    is_base64: bool = False,
) -> dict:
    """Write content to a GCS object. Creates the object if it doesn't exist.

    For binary files (PDFs, images), set is_base64=True and pass
    base64-encoded content.

    Args:
        bucket_name: The GCS bucket name (without gs:// prefix).
        object_name: Full object path within the bucket
                     (e.g. 'customer_123/intervention_001.pdf').
        content: The content to write. Plain text by default,
                 or base64-encoded string if is_base64=True.
        content_type: MIME type (default 'text/plain').
                      Use 'application/pdf' for PDFs.
        is_base64: If True, decode content from base64 before uploading.
    """
    blob = client.bucket(bucket_name).blob(object_name)
    data = base64.b64decode(content) if is_base64 else content
    blob.upload_from_string(data, content_type=content_type)

    public_url = f"https://storage.googleapis.com/{bucket_name}/{object_name}"
    return {
        "bucket": bucket_name,
        "object": object_name,
        "content_type": content_type,
        "gs_uri": f"gs://{bucket_name}/{object_name}",
        "public_url": public_url,
    }


if __name__ == "__main__":
    app = mcp.http_app(transport="streamable-http")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Mcp-Session-Id"],
    )
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
