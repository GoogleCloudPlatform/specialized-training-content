# Setup

Infrastructure provisioning scripts for the Cymbal Meet Agent System.

## Contents

| File | Description |
|------|-------------|
| `setup.sh` | Full provisioning pipeline (Phases 1–8), idempotent |
| `deploy_gcs_mcp.sh` | Standalone GCS MCP server deployment to Cloud Run |
| `generate_data.py` | Creates BigQuery tables and loads ~3.6M rows of synthetic data. Supports `--dry-run` |
| `create_bq_tables.py` | Creates BigQuery dataset and tables only (schema, no data) |
| `upload_reference_docs.py` | Uploads reference PDFs to GCS |
| `create_datastore.py` | Creates Vertex AI Search datastore and imports documents |
| `convert_md_to_pdf.sh` | Converts markdown reference docs to PDF (manual, requires Node.js) |
| `requirements.txt` | Python deps for setup scripts |
| `gcs-mcp-server/` | GCS MCP server source — see [gcs-mcp-server/README.md](gcs-mcp-server/README.md) |

## Prerequisites

- Google Cloud project with billing enabled
- `gcloud` CLI authenticated with Owner or Editor role
- Python 3.11+
- Accept Terms of Service at the [AI Applications console](https://console.cloud.google.com/gen-app-builder) before running — required for Vertex AI Search datastore creation
- Node.js/npm — only needed if regenerating PDFs from markdown source via `convert_md_to_pdf.sh`

## Running setup.sh

```bash
cd setup
./setup.sh                          # prompts for project ID
PROJECT_ID=my-project ./setup.sh    # explicit project (skips prompt)
```

Optional overrides:

```bash
REGION=us-central1 DATASTORE_ID=cymbal-meet-docs ./setup.sh
```

### What it does

| Phase | Description |
|-------|-------------|
| 1 | Enable APIs (Vertex AI, BigQuery, Cloud Run, Discovery Engine, etc.) and the BigQuery MCP endpoint |
| 2 | Create two service accounts: `cymbal-agent@` (agents) and `gcs-mcp-sa@` (GCS MCP server) |
| 3 | Grant IAM roles to both service accounts |
| 4 | Create three GCS buckets: agent staging, reference docs, interventions |
| 5 | Create Python venv, install deps, and upload reference PDFs to GCS |
| 6 | Provision AI Applications and create Vertex AI Search datastore (polls until indexing completes) |
| 7 | Create BigQuery `cymbal_meet` dataset, five tables, and load ~3.6M rows of synthetic data |
| 8 | Deploy GCS MCP server to Cloud Run and grant agent SA invoker access |

Vertex AI Search indexing takes 5–30 minutes. The script polls until complete.

The script is idempotent — safe to re-run.

### After it runs

On success the script prints the GCS MCP endpoint URL, e.g.:

```
GCS MCP endpoint: https://gcs-mcp-server-xxxx.us-central1.run.app/mcp
```

Record this URL — it's required when configuring the Intervention Agent.

## Standalone GCS MCP deployment

`deploy_gcs_mcp.sh` deploys or redeploys the GCS MCP server independently of `setup.sh`. Useful when iterating on the server without re-running the full pipeline.

```bash
./deploy_gcs_mcp.sh
PROJECT_ID=my-project ./deploy_gcs_mcp.sh
```

Requires `setup.sh` to have been run first (APIs, service accounts, and IAM must already exist).

For server details, tools, and local dev instructions see [gcs-mcp-server/README.md](gcs-mcp-server/README.md).
