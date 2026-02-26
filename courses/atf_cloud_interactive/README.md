# Cymbal Meet Customer Engagement Agent System

Multi-agent system (ADK + Agent Engine + A2A + MCP) on Google Cloud that identifies underengaged Cymbal Meet customers and generates tailored intervention PDFs.

## Architecture

Three agents coordinated via A2A:

- **Orchestrator Agent** — Coordinates the pipeline
- **Data Agent** — Queries BigQuery via MCP for customer engagement metrics
- **Intervention Agent** — Retrieves best practices via Vertex AI Search RAG, generates PDF interventions, writes to GCS via MCP

## Directory Structure

```
atf_cloud_interactive/
├── PLAN.md                        # Technical roadmap
├── PRD.md                         # Product requirements
├── agents/
│   ├── requirements.txt           # Shared Python deps for all agents
│   └── data_agent/
│       ├── __init__.py            # ADK boilerplate
│       ├── agent.py               # Data Agent (BQ MCP, schema discovery)
│       ├── .env                   # Environment config
│       └── .env.example           # Template env config
├── reference_docs/
│   ├── markdown/                  # Source docs (5 fictional Cymbal Meet docs)
│   │   ├── admin_guide_user_onboarding.md
│   │   ├── intervention_templates.md
│   │   ├── product_best_practices_guide.md
│   │   ├── troubleshooting_call_quality.md
│   │   └── troubleshooting_device_performance.md
│   └── pdf/                       # Converted PDFs (uploaded to GCS)
└── setup/
    ├── setup.sh                   # Full provisioning pipeline
    ├── deploy_gcs_mcp.sh          # GCS MCP server deployment to Cloud Run
    ├── create_bq_tables.py        # BigQuery dataset + 5 tables (idempotent)
    ├── generate_data.py           # Synthetic data gen (~3.6M rows, --dry-run)
    ├── convert_md_to_pdf.sh       # Markdown → PDF conversion
    ├── upload_reference_docs.py   # Upload PDFs to GCS
    ├── create_datastore.py        # Vertex AI Search datastore + doc import
    ├── requirements.txt           # Python deps for setup scripts
    └── gcs-mcp-server/
        ├── server.py              # FastMCP server (3 tools)
        ├── requirements.txt
        └── Dockerfile
```

## Setup

### Prerequisites

- Google Cloud project with billing enabled
- `gcloud` CLI authenticated and configured
- Owner or Editor role on the project
- Node.js / npm (for `md-to-pdf` conversion and MCP Inspector)

### Phase 1: Infrastructure + Vertex AI Search

```bash
cd setup

# Uses current gcloud project, or override:
# export PROJECT_ID=my-project

./setup.sh
```

This script runs the full provisioning pipeline:
1. Enables required APIs (including BigQuery MCP endpoint)
2. Creates two service accounts (`cymbal-agent@` and `gcs-mcp-sa@`)
3. Assigns IAM roles
4. Creates three GCS buckets (agent staging, reference docs, interventions)
5. Creates a Python venv and installs dependencies
6. Converts reference docs from markdown to PDF
7. Uploads PDFs to the refs GCS bucket
8. Creates a Vertex AI Search datastore and imports docs

The script is idempotent — safe to re-run.

> **Note:** Vertex AI Search requires ToS acceptance at the [AI Applications console](https://console.cloud.google.com/gen-app-builder) before the datastore creation step will succeed.

### Phase 2: BigQuery Data Layer

```bash
# Create dataset and tables
python create_bq_tables.py

# Generate and load synthetic data (~3.6M rows)
python generate_data.py

# Validate without loading (optional)
python generate_data.py --dry-run
```

### Phase 3: GCS MCP Server Deployment

```bash
./deploy_gcs_mcp.sh
```

Builds and deploys the GCS MCP server to Cloud Run via source-based build. On success it prints the MCP endpoint URL (e.g. `https://gcs-mcp-server-xxx.run.app/mcp`).

The server exposes three tools over Streamable HTTP:

| Tool | Description |
|------|-------------|
| `list_objects` | List GCS objects with metadata |
| `read_object` | Read object content as text |
| `write_object` | Write objects (supports base64 for binary/PDF) |

**Verify the deployment:**

```bash
npx @anthropic-ai/mcp-inspector
```

Connect to the `/mcp` endpoint and confirm the three tools are listed.

### Running the Data Agent (local dev)

```bash
cd agents/data_agent
cp .env.example .env   # edit with your project ID
adk web
```
