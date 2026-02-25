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
├── reference_docs/                # Fictional Cymbal Meet docs (for RAG)
│   ├── admin_guide_user_onboarding.md
│   ├── intervention_templates.md
│   ├── product_best_practices_guide.md
│   ├── troubleshooting_call_quality.md
│   └── troubleshooting_device_performance.md
└── setup/
    ├── setup.sh                   # Phase 1: infrastructure provisioning
    ├── deploy_gcs_mcp.sh          # Phase 2: GCS MCP server deployment
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

### Phase 1: Infrastructure Provisioning

```bash
cd setup

# Uses current gcloud project, or override:
# export PROJECT_ID=my-project

./setup.sh
```

This enables required APIs, creates two service accounts (`cymbal-agent@` and `gcs-mcp-sa@`), assigns IAM roles, and creates three GCS buckets (agent staging, reference docs, interventions). The script is idempotent — safe to re-run.

### Phase 2: GCS MCP Server Deployment

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
