# PLAN.md — Cymbal Meet Customer Engagement Agent System

## Project

Multi-agent system (ADK + Agent Engine + A2A + MCP) on Google Cloud that identifies underengaged Cymbal Meet customers and generates tailored intervention PDFs. This is the basis for a hands-on lab on Google Cloud agentic development.

Full spec: [PRD.md](PRD.md)

## Architecture decisions

- 3-agent architecture: Orchestrator → Data Agent (A2A) + Intervention Agent (A2A)
- Data Agent owns all BigQuery/SQL knowledge; Orchestrator never sees the schema
- Intervention Agent uses Vertex AI Search for RAG, WeasyPrint+Jinja2 for PDFs, GCS MCP (Cloud Run) for storage
- BigQuery MCP server is Google-hosted (no deployment needed); GCS MCP deploys to Cloud Run
- Custom service account (`cymbal-agent@`) for agent deployment — explicit and teachable for lab
- Separate service account (`gcs-mcp-sa@`) for the Cloud Run GCS MCP server
- `VertexAiSearchTool` with `bypass_multi_tools_limit=True` (ADK v1.16.0+) — lives directly on Intervention Agent alongside other tools, no sub-agent needed
- All scripts are project-agnostic — parameterized by `$PROJECT_ID` env var with `gcloud config` fallback, so they work in any lab project without edits
- Infrastructure scripts are idempotent (safe to re-run) — important for lab environments where students may retry steps
- GCS MCP server is a custom Python FastMCP server wrapping `google-cloud-storage` — deployed to Cloud Run with Streamable HTTP at `/mcp`. Replaces the earlier supergateway+npm approach (stdio bridge was unnecessarily complex). Google doesn't yet offer a managed GCS MCP endpoint like BigQuery's.
- Reference docs are authored as markdown in `reference_docs/markdown/`, converted to PDF via `convert_md_to_pdf.sh`, and uploaded as PDFs to GCS for Vertex AI Search ingestion
- Reference doc content is deliberately aligned to the 5 problem customer profiles in PRD 3.4 — each problem customer's root cause maps to specific retrievable sections across the docs, so the Intervention Agent's RAG queries will return actionable content
- Synthetic data is hand-designed profiles + programmatic generation — the 25 customers and 5 problem profiles are hand-specified in PRD 3.4, but the ~3.6M data rows (dominated by device telemetry) are generated via seeded numpy RNG (`generate_data.py`). This gives deterministic, reproducible data with obvious outliers detectable via simple SQL GROUP BY queries
- Device telemetry is 1 reading/device every 5 minutes during business hours (8am–6pm weekdays) — ~3.1M rows across 746 devices × 120 readings/day × 35 weekdays
- Data gen loads via in-memory JSONL → `load_table_from_file` with `WRITE_TRUNCATE` — idempotent, no temp files on disk. Telemetry table (~3M rows) is the bottleneck; logins/calls/events are fast
- `create_bq_tables.py` and `generate_data.py` are separate scripts — schema creation is fast/idempotent, data gen is slow and benefits from `--dry-run` for validation without a GCP project
- MCP auth uses ADK's `auth_scheme`/`auth_credential` pipeline — OAuth2 clientCredentials + SERVICE_ACCOUNT with `use_default_credential=True`. Handles token refresh automatically, follows the official `mcp_service_account_agent` sample pattern. Replaces earlier manual `fetch_id_token()` + headers approach
- Deployment uses `adk deploy agent_engine` CLI (not Python SDK). Each agent has `.env.deploy` (runtime env vars) and `.agent_engine_config.json` (service account, scaling) as deployment config. Template `.example` files are checked in; actual configs are gitignored

## Key files

### Setup & infrastructure
- `setup/setup.sh` — full provisioning pipeline (Phases 1–8): APIs, SAs, IAM, buckets, Python venv + ref doc upload, Vertex AI Search datastore, BigQuery data gen, GCS MCP deployment to Cloud Run. Includes validation checks at the end
- `setup/deploy_gcs_mcp.sh` — standalone alternative for deploying GCS MCP to Cloud Run (setup.sh Phase 8 does this too)
- `setup/requirements.txt` — Python deps for setup scripts

### BigQuery data layer
- `setup/create_bq_tables.py` — creates `cymbal_meet` dataset + 5 tables (schema only, idempotent)
- `setup/generate_data.py` — creates tables + deterministic synthetic data gen (~3.6M rows), loads via JSONL. Supports `--dry-run`

### GCS MCP server
- `setup/gcs-mcp-server/server.py` — FastMCP server (list/read/write)
- `setup/gcs-mcp-server/Dockerfile` — Cloud Run container definition
- `setup/gcs-mcp-server/requirements.txt` — server Python deps

### Reference docs & search
- `reference_docs/markdown/*.md` — 5 Cymbal Meet docs (source)
- `reference_docs/pdf/*.pdf` — pre-generated PDFs uploaded to GCS for Vertex AI Search
- `setup/convert_md_to_pdf.sh` — regenerates PDFs from markdown via `npx md-to-pdf` (manual, requires Node.js)
- `setup/upload_reference_docs.py` — uploads PDFs to GCS
- `setup/create_datastore.py` — creates Vertex AI Search datastore, imports + indexes docs

### Data Agent
- `agents/data_agent/__init__.py` — ADK boilerplate (`from . import agent`)
- `agents/data_agent/agent.py` — Data Agent: BQ MCP toolset (auth_scheme/auth_credential), system prompt, `root_agent` + `AdkApp`
- `agents/data_agent/requirements.txt` — agent-specific Python deps
- `agents/data_agent/.env.example` — local dev env vars template (PROJECT_ID, location, Vertex AI flags)
- `agents/requirements.txt` — shared Python deps for all agents

### Deployment
Deployment configs are gitignored. The repo contains `.example` templates; copy and replace placeholders with your project values:
- `agents/deploy_data_agent.example.sh` → `deploy_data_agent.sh` — deployment script (`adk deploy agent_engine`)
- `agents/data_agent/.env.example` → `.env` — local dev env vars (project, location, Vertex AI flags)
- `agents/data_agent/.env.deploy.example` → `.env.deploy` — runtime env vars (staging bucket, telemetry flags)
- `agents/data_agent/.agent_engine_config.example.json` → `.agent_engine_config.json` — Agent Engine config (service account, scaling)

### Test & debug utilities
- `test/t1.py` — test deployed agent via async streaming
- `test/list_engines.py` — list all Agent Engine deployments
- `test/del_engines.py` — delete Agent Engine deployments
- `test/inter-test.sh` — Cloud Run deployment test
- `test/pull.py` — pull Cloud Logging entries to JSON
- `test/requirements.txt` — test script deps

### Archive
- `archive/` — superseded file versions (reference only)

## Completed

- [x] Setup scripts — infra provisioning (APIs, 2 service accounts, IAM, 3 buckets)
- [x] GCS MCP server — custom FastMCP on Cloud Run with Streamable HTTP (`/mcp`)
- [x] Reference docs — 5 fictional Cymbal Meet docs aligned to PRD 3.4 problem profiles
- [x] Vertex AI Search — datastore creation, GCS import, indexing with polling
- [x] BigQuery data layer — `create_bq_tables.py` (dataset + 5 tables) + `generate_data.py` (seeded numpy RNG, ~3.6M rows, 5 problem profiles with obvious outliers, `--dry-run` support)
- [x] Data Agent (Steps 1–5) — directory structure, BQ MCP toolset (`auth_scheme`/`auth_credential`: OAuth2 clientCredentials + SERVICE_ACCOUNT with `use_default_credential=True`), system prompt (runtime schema discovery via MCP tools, UNNEST handling, read-only constraint), `root_agent` definition (`gemini-3-flash-preview` with `Gemini3` subclass for `location='global'`), environment config (`PROJECT_ID` with gcloud fallback)
- [x] Data Agent deployment — `deploy_data_agent.sh` with `adk deploy agent_engine`, Agent Engine config (`.agent_engine_config.json`), deploy env (`.env.deploy`), `AdkApp` wrapper in `agent.py`

## Jeff's Exploration Tasks

- [x] add to_a2a
- [x] ran locally with uvicorn data_agent.agent:a2a_app --port 8080
- [x] tested with a2a inspector; it all works (basic client interaction)
- [ ] test deploying to cloud run


## Tasks — Data Agent A2A enablement

Goal: make the Data Agent callable via A2A so the Orchestrator can delegate data questions to it (PRD 2.2). The Data Agent is already deployed to Agent Engine as an `AdkApp`; it needs the A2A server layer and agent card so it can receive A2A tasks.

- [ ] Research how ADK + Agent Engine expose agents via A2A — does Agent Engine handle A2A automatically for deployed `AdkApp` agents, or do we need an explicit A2A server wrapper? Check ADK docs / `a2a-sdk` for the integration pattern
- [ ] Add `a2a-sdk` to `agents/requirements.txt` and `agents/data_agent/requirements.txt` if not already bundled with `google-adk`
- [ ] Define A2A agent card for the Data Agent — name, description, skills/capabilities (natural language data questions → structured results), input/output content types
- [ ] Add A2A server wrapper to Data Agent (if needed beyond Agent Engine's built-in support) — wrap the existing `root_agent` / `AdkApp` so it handles A2A task requests
- [ ] Test A2A connectivity — send a task to the deployed Data Agent via an A2A client and verify it receives the question, queries BigQuery via MCP, and returns structured results
- [ ] Update deployment config and redeploy if the A2A changes require it

## Upcoming (ordered)
- [ ] Intervention Agent — RAG retrieval via Vertex AI Search, PDF generation (Jinja2 + WeasyPrint), GCS write via MCP, A2A-enabled
- [ ] Orchestrator Agent — coordinates Data + Intervention agents via A2A
- [ ] Deployment — remaining agents to Agent Engine, orchestrator published to Gemini Enterprise (Data Agent already deployed)
- [ ] End-to-end validation — test the full flow from PRD section 10

## Vague future things (don't plan yet)

- Lab instructions / student guide (how to deconstruct and rebuild)
- Scaffolding for early lab sections vs. open-ended final section
- README.md for the repo

## Resolved questions

- **Build order for agents**: Dev order: Data Agent first (simpler, proves BQ MCP), then decide next. Lab order: Data Agent → Orchestrator → Intervention Agent. Students may do AI Applications ToS + Vertex AI Search setup early to allow indexing time.
- **Local dev vs. cloud-first**: Develop and test locally with ADK first, then deploy to Agent Engine.
- **VertexAiSearchTool constraint**: ADK v1.16.0+ supports `bypass_multi_tools_limit=True` parameter directly on `VertexAiSearchTool`. No sub-agent or custom wrapper needed — the tool lives directly on the Intervention Agent alongside PDF/GCS tools.
- **PDF template fidelity**: Demo-quality with branding.
- **Reference doc format for Vertex AI Search**: Switched from raw markdown to PDF. Markdown source in `reference_docs/markdown/` is converted via `convert_md_to_pdf.sh` (`npx md-to-pdf`), and PDFs are uploaded to GCS for ingestion.
- **Data gen deployment strategy**: `generate_data.py` produces deterministic output via seeded RNG. For lab deployment, pre-generate JSONL files and host in a shared GCS bucket so students load via `bq load` without needing Python/numpy locally. The script itself is for development and pre-generation.
- **Telemetry generation memory/time**: In-memory generation of ~3.1M telemetry rows completes without issue — no OOM or excessive runtime observed.

## Open questions
- **Data freshness for lab delivery**: Date range is relative to generation date (7 weeks ending on most recent Sunday). Pre-generated JSONL files will have fixed dates — acceptable? Or should students run `generate_data.py` themselves so dates are always fresh?

## Assumptions and gotchas

- PRD specifies ~25 customers with ~3-4 exhibiting clear engagement problems — data gen must be deliberate, not purely random
- Vertex AI Search indexing takes 5-30 minutes — start Phase 3 early in setup
- GCS MCP server is custom Python (FastMCP + google-cloud-storage) — not the `@google-cloud/storage-mcp` npm package. Google doesn't have a managed GCS MCP endpoint yet, and the npm package is stdio-only (would need a bridge for Cloud Run)
- Intervention bucket needs public read access configured for PDF URLs to work
- Agent Engine staging bucket (`gs://$PROJECT_ID-agent-staging`) is required before any agent deployment
- The provisioning order in PRD section 7.2 has real dependency constraints — don't parallelize carelessly
- AI Applications console (gen-app-builder) requires manual ToS acceptance — can't be fully automated
- `gcloud projects add-iam-policy-binding` with `--condition=None` is needed to avoid interactive prompts in scripts — discovered during setup.sh build
- `gsutil iam ch allUsers:objectViewer` for the interventions bucket may hit org policy constraints in locked-down lab environments — may need a fallback (signed URLs or proxy)
- Reference docs use fictional but internally consistent product details (firmware versions, DSCP values, bandwidth thresholds, quality score scales) — these must stay consistent with the synthetic data baselines in PRD 3.4 (e.g., healthy video_quality_score mean of 4.2 matches the "Good" threshold in the troubleshooting guides)
- `generate_data.py` uses `WRITE_TRUNCATE` disposition — re-running replaces all data rather than appending duplicates. This is the right default for idempotent lab scripts but means you can't incrementally add data
- BrightPath (declining usage) decline curve is `[1.0, 1.0, 1.0, 0.85, 0.65, 0.45, 0.35]` across 7 weeks — applied to logins, calls, and calendar events. Week-over-week decline should be clearly visible in SQL `GROUP BY EXTRACT(WEEK FROM ...)` queries
- Pinnacle (low login adoption) generates emails for only ~25% of licensed users — the `COUNT(DISTINCT user_email) / licensed_users` signal depends on this, not just lower login frequency
- `customers` table uses a `REPEATED RECORD` for interactions (BigQuery nested/repeated fields) — the Data Agent's system prompt must document this nested structure so the LLM generates correct `UNNEST()` SQL
- BigQuery MCP endpoint requires a separate enablement (`gcloud beta services mcp enable bigquery.googleapis.com`) beyond the standard `gcloud services enable bigquery.googleapis.com`. Without it, `tools/list` succeeds but `tools/call` returns 403. Added to `setup.sh`
- Gemini 3 models require `location='global'` — incompatible with Agent Engine which needs a regional location (e.g., `us-central1`). Implemented workaround in Data Agent: `Gemini3(Gemini)` subclass that overrides `api_client` to force `location='global'`. 
- ADC user credentials ignore the `scopes` parameter in `google.auth.default()` — the token carries whatever scopes were granted at `gcloud auth application-default login` time. Use `cloud-platform` scope (the default) rather than narrow scopes like `bigquery`