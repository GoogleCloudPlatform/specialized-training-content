# GCS MCP Server

A lightweight [FastMCP](https://github.com/jlowin/fastmcp) server that exposes Google Cloud Storage operations as tools over Streamable HTTP. Deployed to Cloud Run and used by the Intervention Agent to interact with GCS without passing binary file content through the MCP layer.

**Endpoint:** `POST /mcp` (Streamable HTTP transport)

## Tools

| Tool | Description |
|------|-------------|
| `list_objects` | List objects in a bucket, optionally filtered by prefix |
| `read_object` | Read a text object's content (small files only) |
| `generate_upload_signed_url` | Generate a V4 signed URL for direct PUT upload |
| `generate_download_signed_url` | Generate a V4 signed URL for direct GET download |

For binary files (PDFs, images), use the signed URL tools to bypass the MCP layer.

## IAM Requirements

The Cloud Run service account needs:

- `roles/storage.objectViewer` (or `objectAdmin`) on the target bucket
- `roles/iam.serviceAccountTokenCreator` on **itself** — required for `signBlob` when generating signed URLs

> **Note:** Full project setup via `setup/setup.sh` grants `roles/storage.objectAdmin` at the project level (a superset of the bucket-level permissions listed above), so no additional bucket-level grants are needed when using the standard provisioning path.

## Local Development

### 1. Service Account Key

Download a JSON key for the service account that will be used for the Cloud Run deployment. This ensures local signed URL generation matches the production identity.

```bash
gcloud iam service-accounts keys create key.json \
  --iam-account=YOUR_SA@YOUR_PROJECT.iam.gserviceaccount.com
```

> Keep `key.json` out of version control — it's already in `.gitignore`.

### 2. Configure Application Default Credentials

Point ADC at the key file so the server authenticates as the service account:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/key.json"
```

Add this to your shell profile or set it in each terminal session before running the server.

### 3. Create a Virtual Environment

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 4. Run the Server

```bash
python server.py
# Listening on http://localhost:8080
# MCP endpoint: http://localhost:8080/mcp
```

### 5. Test with MCP Inspector

[MCP Inspector](https://github.com/modelcontextprotocol/inspector) provides a browser UI for calling tools interactively.

```bash
npx @modelcontextprotocol/inspector
```

When prompted for a connection, choose **Streamable HTTP** and enter:

```
http://localhost:8080/mcp
```

You can then list and invoke tools (`list_objects`, `read_object`, etc.) directly from the UI.

---

> **Testing the deployed service?** See [test/README.md](../../test/README.md#testing-the-gcs-mcp-server-on-cloud-run) for instructions on using the Cloud Run proxy with MCP Inspector.

## Deployment

To deploy this server on its own (after `setup.sh` has already provisioned APIs, service accounts, and IAM):

```bash
./setup/deploy_gcs_mcp.sh
```

The server is also deployed automatically as part of full project setup:

```bash
./setup/setup.sh   # Phase 8 deploys the GCS MCP server
```

The `PORT` environment variable is set automatically by Cloud Run.

## Dependencies

- `fastmcp>=2.0`
- `google-auth>=2.0`
- `google-cloud-storage>=2.18`
- `uvicorn>=0.32`
