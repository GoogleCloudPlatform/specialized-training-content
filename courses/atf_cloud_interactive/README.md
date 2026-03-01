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
├── .gitignore
├── agents/
│   ├── requirements.txt           # Shared Python deps for all agents
│   ├── deploy_data_agent.example.sh  # Deployment script template (copy → deploy_data_agent.sh)
│   └── data_agent/
│       ├── __init__.py            # ADK boilerplate
│       ├── agent.py               # Data Agent (BQ MCP, schema discovery)
│       ├── requirements.txt       # Agent-specific Python deps
│       ├── .env                   # Environment config (gitignored)
│       ├── .env.deploy.example    # Deploy env vars template (copy → .env.deploy)
│       └── .agent_engine_config.example.json  # Agent Engine config template (copy → .agent_engine_config.json)
├── reference_docs/
│   ├── markdown/                  # Source docs (5 fictional Cymbal Meet docs)
│   │   ├── admin_guide_user_onboarding.md
│   │   ├── intervention_templates.md
│   │   ├── product_best_practices_guide.md
│   │   ├── troubleshooting_call_quality.md
│   │   └── troubleshooting_device_performance.md
│   └── pdf/                       # Pre-generated PDFs (uploaded to GCS)
├── setup/
│   ├── setup.sh                   # Full provisioning pipeline
│   ├── deploy_gcs_mcp.sh          # GCS MCP server deployment to Cloud Run
│   ├── create_bq_tables.py        # BigQuery dataset + 5 tables (idempotent)
│   ├── generate_data.py           # Synthetic data gen (~3.6M rows, --dry-run)
│   ├── convert_md_to_pdf.sh       # Markdown → PDF conversion (manual, requires Node.js)
│   ├── upload_reference_docs.py   # Upload PDFs to GCS
│   ├── create_datastore.py        # Vertex AI Search datastore + doc import
│   ├── requirements.txt           # Python deps for setup scripts
│   └── gcs-mcp-server/
│       ├── server.py              # FastMCP server (3 tools)
│       ├── requirements.txt
│       └── Dockerfile
├── test/                          # Test & debug utilities for deployed agents
└── archive/                       # Superseded file versions (reference only)
```

## Setup

### Prerequisites

- Google Cloud project with billing enabled
- `gcloud` CLI authenticated and configured
- Owner or Editor role on the project
- Node.js / npm (for MCP Inspector testing; also needed if re-generating PDFs from markdown via `convert_md_to_pdf.sh`)

### Phase 1: Infrastructure Provisioning

```bash
cd setup

# Uses current gcloud project, or override:
# export PROJECT_ID=my-project

./setup.sh
```

This script runs the full provisioning pipeline (Phases 1–7):
1. Enables required APIs (including BigQuery MCP endpoint)
2. Creates two service accounts (`cymbal-agent@` and `gcs-mcp-sa@`)
3. Assigns IAM roles
4. Creates three GCS buckets (agent staging, reference docs, interventions)
5. Creates a Python venv and installs dependencies
6. Uploads pre-generated PDFs to the refs GCS bucket
7. Provisions AI Applications and creates a Vertex AI Search datastore with doc import
8. Creates BigQuery dataset, tables, and loads synthetic data (~3.6M rows)

The script is idempotent — safe to re-run.

> **Note:** Vertex AI Search requires ToS acceptance at the [AI Applications console](https://console.cloud.google.com/gen-app-builder) before the datastore creation step will succeed.

### Phase 2: GCS MCP Server Deployment

```bash
./deploy_gcs_mcp.sh
```

Builds and deploys the GCS MCP server to Cloud Run via source-based build. On success it prints the MCP endpoint URL (e.g. `https://gcs-mcp-server-xxx.run.app/mcp`).

The server exposes three tools over Streamable HTTP:

| Tool           | Description                                    |
| -------------- | ---------------------------------------------- |
| `list_objects` | List GCS objects with metadata                 |
| `read_object`  | Read object content as text                    |
| `write_object` | Write objects (supports base64 for binary/PDF) |

**Verify the deployment:**

```bash
npx @anthropic-ai/mcp-inspector
```

Connect to the `/mcp` endpoint and confirm the three tools are listed.

### Running the Data Agent

#### Local dev

```bash
cd agents/data_agent
# edit .env with your project ID
adk web
```

#### Deploy to Agent Engine

```bash
cd agents

# Copy templates and fill in your project values
cp deploy_data_agent.example.sh deploy_data_agent.sh
cp data_agent/.env.deploy.example data_agent/.env.deploy
cp data_agent/.agent_engine_config.example.json data_agent/.agent_engine_config.json

# Edit each file to replace placeholders, then deploy
bash deploy_data_agent.sh
```

The deploy script runs `adk deploy agent_engine`. On success it prints the Agent Engine resource name, which you can use to test the deployed agent.