"""GCS MCP Server — Cloud Run deployment.

A lightweight MCP server that exposes Google Cloud Storage operations
as tools over Streamable HTTP. Deployed to Cloud Run, called by the
Intervention Agent to read/list objects and generate signed URLs for
direct uploads and downloads (bypassing the MCP layer for file content).

Endpoint: /mcp (Streamable HTTP transport)
"""

import datetime
import os

import google.auth
import google.auth.transport.requests
import uvicorn
from fastmcp import FastMCP
from google.cloud import storage
from starlette.middleware.cors import CORSMiddleware

mcp = FastMCP("GCS Storage")

client = storage.Client()

# Credentials for signed URL generation (requires service account on Cloud Run).
# The service account must have iam.serviceAccounts.signBlob on itself
# (granted via roles/iam.serviceAccountTokenCreator on the SA resource).
_credentials, _ = google.auth.default()
_auth_request = google.auth.transport.requests.Request()


def _refresh_credentials():
    """Refresh credentials to ensure a valid access token for signing."""
    _credentials.refresh(_auth_request)


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

    Suitable for small text files only. For binary files (PDFs, images),
    use generate_download_signed_url instead to avoid passing content
    through the MCP layer.

    Args:
        bucket_name: The GCS bucket name (without gs:// prefix).
        object_name: Full object path within the bucket (e.g. 'config/settings.json').
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
def generate_upload_signed_url(
    bucket_name: str,
    object_name: str,
    content_type: str = "application/pdf",
    expiration_minutes: int = 15,
) -> dict:
    """Generate a V4 signed URL for uploading a file directly to GCS.

    Use this for binary file uploads (PDFs, images) instead of passing
    file content through the MCP layer. The caller should HTTP PUT the
    file bytes to the returned signed_url with a matching Content-Type header.

    Args:
        bucket_name: The GCS bucket name (without gs:// prefix).
        object_name: Full object path (e.g. 'customer_123/intervention.pdf').
        content_type: MIME type of the file to upload (default 'application/pdf').
        expiration_minutes: URL validity in minutes (default 15, max 60 for V4).

    Returns:
        dict with signed_url (PUT to this), method, content_type, gs_uri,
        public_url, and expires_in_minutes.
    """
    _refresh_credentials()
    blob = client.bucket(bucket_name).blob(object_name)
    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=expiration_minutes),
        method="PUT",
        content_type=content_type,
        service_account_email=_credentials.service_account_email,
        access_token=_credentials.token,
    )
    return {
        "signed_url": signed_url,
        "method": "PUT",
        "content_type": content_type,
        "gs_uri": f"gs://{bucket_name}/{object_name}",
        "public_url": f"https://storage.googleapis.com/{bucket_name}/{object_name}",
        "expires_in_minutes": expiration_minutes,
    }


@mcp.tool
def generate_download_signed_url(
    bucket_name: str,
    object_name: str,
    expiration_minutes: int = 60,
) -> dict:
    """Generate a V4 signed URL for downloading a GCS object directly.

    Use this for binary file downloads (PDFs, images) instead of read_object,
    to avoid passing file content through the MCP layer.

    Args:
        bucket_name: The GCS bucket name (without gs:// prefix).
        object_name: Full object path (e.g. 'customer_123/intervention.pdf').
        expiration_minutes: URL validity in minutes (default 60, max 10080 for V4).

    Returns:
        dict with signed_url (GET this), method, gs_uri, and expires_in_minutes.
    """
    _refresh_credentials()
    blob = client.bucket(bucket_name).blob(object_name)
    signed_url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=expiration_minutes),
        method="GET",
        service_account_email=_credentials.service_account_email,
        access_token=_credentials.token,
    )
    return {
        "signed_url": signed_url,
        "method": "GET",
        "gs_uri": f"gs://{bucket_name}/{object_name}",
        "expires_in_minutes": expiration_minutes,
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
