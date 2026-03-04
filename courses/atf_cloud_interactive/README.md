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
│   ├── deploy_data_agent_to_agent_engine.sh           # Deployment script (set env vars before running)
│   ├── deploy_orch_agent_to_agent_engine.sh           # Deployment script (set env vars before running)
│   ├── data_agent/
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

See [setup/README.md](setup/README.md) for infrastructure provisioning (APIs, service accounts, IAM, GCS buckets, Vertex AI Search, BigQuery, and GCS MCP server).

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
cp data_agent/.env.deploy.example data_agent/.env.deploy
cp data_agent/.agent_engine_config.example.json data_agent/.agent_engine_config.json
# Edit each file to replace placeholders

# Set required env vars before deploying
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_LOCATION=us-central1

bash deploy_data_agent_to_agent_engine.sh
```

The deploy script runs `adk deploy agent_engine`. On success it prints the Agent Engine resource name, which you can use to test the deployed agent.

### Running the Orchestrator Agent

#### Local dev

```bash
cd agents/orchestrator
# edit .env with your project ID
adk web
```

#### Deploy to Agent Engine

```bash
cd agents

# Copy templates and fill in your project values
cp orchestrator/.env.deploy.example orchestrator/.env.deploy
cp orchestrator/.agent_engine_config.example.json orchestrator/.agent_engine_config.json
# Edit each file to replace placeholders

# Set required env vars before deploying
export GOOGLE_CLOUD_PROJECT=your-project-id
export GOOGLE_CLOUD_LOCATION=us-central1

bash deploy_orch_agent_to_agent_engine.sh
```

The deploy script runs `adk deploy agent_engine`. On success it prints the Agent Engine resource name, which you can use to test the deployed agent.