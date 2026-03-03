# PLAN.md — Cymbal Meet Customer Engagement Agent System

## Project

Multi-agent system (ADK + Agent Engine + A2A + MCP) on Google Cloud that identifies underengaged Cymbal Meet customers and generates tailored intervention PDFs. This is the basis for a hands-on lab on Google Cloud agentic development.

Full spec: [PRD.md](PRD.md)

## Architecture decisions

- 3-agent architecture: Orchestrator → Data Agent (A2A) + Intervention Agent (A2A)
- **Deployment split**: Data Agent and Intervention Agent deploy to **Cloud Run** as A2A services; Orchestrator deploys to **Agent Engine** and is published to Gemini Enterprise. This split exists because deploying MCP/A2A agents to Agent Engine hit compatibility issues. Long-term goal: migrate all agents to Agent Engine (see PRD section 11)
- Data Agent and Intervention Agent use `to_a2a()` from ADK + uvicorn on Cloud Run; Orchestrator uses `AdkApp` for Agent Engine
- The Orchestrator calls Data/Intervention agents via their Cloud Run A2A URLs; the Orchestrator SA needs `roles/run.invoker` on each Cloud Run service
- Data Agent owns all BigQuery/SQL knowledge; Orchestrator never sees the schema
- Intervention Agent uses Vertex AI Search for RAG, WeasyPrint+Jinja2 for PDFs, GCS MCP (Cloud Run) for storage
- BigQuery MCP server is Google-hosted (no deployment needed); GCS MCP deploys to Cloud Run
- Custom service account (`cymbal-agent@`) for agent deployment — explicit and teachable for lab
- Separate service account (`gcs-mcp-sa@`) for the Cloud Run GCS MCP server
- `VertexAiSearchTool` with `bypass_multi_tools_limit=True` (ADK v1.16.0+) — lives directly on Intervention Agent alongside other tools, no sub-agent needed
- All scripts are project-agnostic — parameterized by `$PROJECT_ID` env var with `gcloud config` fallback, so they work in any lab project without edits
- Infrastructure scripts are idempotent (safe to re-run) — important for lab environments where students may retry steps
- GCS MCP server is a custom Python FastMCP server wrapping `google-cloud-storage` — deployed to Cloud Run with Streamable HTTP at `/mcp`. Replaces the earlier supergateway+npm approach (stdio bridge was unnecessarily complex). Google doesn't yet offer a managed GCS MCP endpoint like BigQuery's.
- GCS MCP uses **signed URLs for file I/O**: `generate_upload_signed_url` and `generate_download_signed_url` return V4 signed URLs so the agent uploads/downloads directly to GCS without passing binary content through the MCP protocol layer. Only small metadata (bucket, object name, URL) passes through MCP. `list_objects` and `read_object` (text-only) remain unchanged. `write_object` is removed. The Intervention Agent uploads via a local `upload_to_signed_url` tool (httpx PUT), and `generate_pdf_from_template` now returns a temp file path instead of a base64 string to keep PDF bytes out of the LLM context entirely.
- Reference docs are authored as markdown in `reference_docs/markdown/`, converted to PDF via `convert_md_to_pdf.sh`, and uploaded as PDFs to GCS for Vertex AI Search ingestion
- Reference doc content is deliberately aligned to the 5 problem customer profiles in PRD 3.4 — each problem customer's root cause maps to specific retrievable sections across the docs, so the Intervention Agent's RAG queries will return actionable content
- Synthetic data is hand-designed profiles + programmatic generation — the 25 customers and 5 problem profiles are hand-specified in PRD 3.4, but the ~3.6M data rows (dominated by device telemetry) are generated via seeded numpy RNG (`generate_data.py`). This gives deterministic, reproducible data with obvious outliers detectable via simple SQL GROUP BY queries
- Device telemetry is 1 reading/device every 5 minutes during business hours (8am–6pm weekdays) — ~3.1M rows across 746 devices × 120 readings/day × 35 weekdays
- Data gen loads via in-memory JSONL → `load_table_from_file` with `WRITE_TRUNCATE` — idempotent, no temp files on disk. Telemetry table (~3M rows) is the bottleneck; logins/calls/events are fast
- `create_bq_tables.py` and `generate_data.py` are separate scripts — schema creation is fast/idempotent, data gen is slow and benefits from `--dry-run` for validation without a GCP project
- MCP auth uses ADK's `auth_scheme`/`auth_credential` pipeline — OAuth2 clientCredentials + SERVICE_ACCOUNT with `use_default_credential=True`. Handles token refresh automatically, follows the official `mcp_service_account_agent` sample pattern. Replaces earlier manual `fetch_id_token()` + headers approach
- Orchestrator deploys to Agent Engine via `adk deploy agent_engine` CLI with `.env.deploy` and `.agent_engine_config.json`. It is NOT an A2A service — it is the A2A client that calls the other agents. Data/Intervention agents deploy to Cloud Run via `gcloud run deploy` with Dockerfiles and `deploy_to_run.sh` scripts

## Key files

### Setup & infrastructure
See [setup/README.md](setup/README.md) for full provisioning instructions and script descriptions.

- `setup/setup.sh` — full provisioning pipeline (Phases 1–8): APIs, SAs, IAM, buckets, Python venv + ref doc upload, Vertex AI Search datastore, BigQuery data gen, GCS MCP deployment to Cloud Run. Includes validation checks at the end
- `setup/deploy_gcs_mcp.sh` — standalone alternative for deploying GCS MCP to Cloud Run (setup.sh Phase 8 does this too)
- `setup/requirements.txt` — Python deps for setup scripts

### BigQuery data layer
- `setup/create_bq_tables.py` — creates `cymbal_meet` dataset + 5 tables (schema only, idempotent)
- `setup/generate_data.py` — creates tables + deterministic synthetic data gen (~3.6M rows), loads via JSONL. Supports `--dry-run`

### GCS MCP server
- `setup/gcs-mcp-server/server.py` — FastMCP server: `list_objects`, `read_object` (text), `generate_upload_signed_url`, `generate_download_signed_url`
- `setup/gcs-mcp-server/Dockerfile` — Cloud Run container definition
- `setup/gcs-mcp-server/requirements.txt` — server Python deps

### Reference docs & search
- `reference_docs/markdown/*.md` — 5 Cymbal Meet docs (source)
- `reference_docs/pdf/*.pdf` — pre-generated PDFs uploaded to GCS for Vertex AI Search
- `setup/convert_md_to_pdf.sh` — regenerates PDFs from markdown via `npx md-to-pdf` (manual, requires Node.js)
- `setup/upload_reference_docs.py` — uploads PDFs to GCS
- `setup/create_datastore.py` — creates Vertex AI Search datastore, imports + indexes docs

### Data Agent (Cloud Run + A2A)
- `agents/data_agent/__init__.py` — ADK boilerplate (`from . import agent`)
- `agents/data_agent/agent.py` — Data Agent: BQ MCP toolset (auth_scheme/auth_credential), system prompt, `root_agent` + `to_a2a()`
- `agents/data_agent/agent_card.json` — A2A agent capability card (protocol v0.3.0, JSONRPC)
- `agents/data_agent/Dockerfile` — Cloud Run container definition (uvicorn serving `a2a_app`)
- `agents/data_agent/deploy_to_run.sh` — Cloud Run deployment script (`gcloud run deploy`)
- `agents/data_agent/requirements.txt` — agent-specific Python deps
- `agents/data_agent/.env.example` — local dev env vars template (PROJECT_ID, location, Vertex AI flags)
- `agents/requirements.txt` — shared Python deps for all agents

### Orchestrator Agent (Agent Engine)
- `agents/orchestrator/__init__.py` — ADK boilerplate (`from . import agent`)
- `agents/orchestrator/agent.py` — Orchestrator: `RemoteA2aAgent` A2A client to Data Agent (OIDC auth via `_CloudRunAuth`), `LlmAgent` `root_agent` with data_agent as sub_agent
- `agents/orchestrator/requirements.txt` — agent-specific Python deps
- `agents/orchestrator/.env.example` — local dev env vars template (PROJECT_ID, DATA_AGENT_URL)
- `agents/orchestrator/.env.deploy.example` — Agent Engine runtime env vars template (staging bucket, telemetry, DATA_AGENT_URL)
- `agents/orchestrator/.agent_engine_config.example.json` — Agent Engine config template (service account, scaling)

### Deployment
**Cloud Run agents (Data Agent, Intervention Agent):** Each agent has a `Dockerfile`, `agent_card.json`, and `deploy_to_run.sh`. Deploy via `gcloud run deploy` with `--no-allow-unauthenticated`. The A2A endpoint is served by uvicorn at port 8080.

**Orchestrator (Agent Engine):** Deployment configs are gitignored. The repo contains `.example` templates; copy and replace placeholders with your project values:
- `agents/orchestrator/.env.example` → `.env` — local dev env vars
- `agents/orchestrator/.env.deploy.example` → `.env.deploy` — runtime env vars (staging bucket, telemetry, Cloud Run agent URLs)
- `agents/orchestrator/.agent_engine_config.example.json` → `.agent_engine_config.json` — Agent Engine config (service account, scaling)

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
- [x] Data Agent — BQ MCP toolset (`auth_scheme`/`auth_credential`), system prompt (runtime schema discovery, UNNEST handling, read-only), `root_agent` (`gemini-3-flash-preview` with `Gemini3` subclass for `location='global'`)
- [x] Data Agent A2A + Cloud Run deployment — `to_a2a()` wrapper, `agent_card.json`, Dockerfile, `deploy_to_run.sh`, Cloud Run telemetry (OpenTelemetry → Cloud Trace/Logging). Deployed and tested at `https://data-agent-HASH.us-central1.run.app`
- [x] Orchestrator Agent (data-only, Agent Engine) — `RemoteA2aAgent` A2A client with OIDC auth to Data Agent Cloud Run URL, `LlmAgent` root with data_agent sub_agent, system prompt for data delegation. Deployed to Agent Engine and validated end-to-end (e.g., "Which customers have the lowest login rates?")
- [x] Intervention Agent (Cloud Run + A2A) — `VertexAiSearchTool` for RAG, `McpToolset` for GCS write, Jinja2+WeasyPrint PDF generation helper, `LlmAgent` orchestrator. Directory structure, Dockerfile, `deploy_to_run.sh`, and A2A enablement complete

## Upcoming (ordered)

### Intervention Agent (Cloud Run + A2A)
- [x] Directory structure — `agents/intervention_agent/` with `__init__.py`, `agent.py`, `agent_card.json`, `Dockerfile`, `deploy_to_run.sh`, `requirements.txt`, `.env.example`
- [x] Agent implementation — Vertex AI Search RAG (`VertexAiSearchTool` with `bypass_multi_tools_limit=True`), PDF generation helper (Jinja2 + WeasyPrint), GCS write via MCP (`McpToolset` with auth pipeline)
- [x] A2A enablement — `to_a2a()` wrapper + agent_card.json (same pattern as Data Agent)
- [x] Cloud Run deployment — Dockerfile, `deploy_to_run.sh`, test A2A endpoint

### Orchestrator — add Intervention Agent
- [ ] Wire Intervention Agent A2A call into Orchestrator — add second A2A client, update system prompt for full workflow (data → intervention → PDF)
- [ ] IAM — grant orchestrator SA `roles/run.invoker` on Intervention Agent Cloud Run service
- [ ] Redeploy Orchestrator to Agent Engine with updated config
- [ ] Publish to Gemini Enterprise

### Integration & Validation
- [ ] End-to-end validation — test the full flow from PRD section 10 (Gemini Enterprise → Orchestrator → Data Agent → Intervention Agent → PDF output)

### Future: Agent Engine Migration
- [ ] Revisit deploying Data Agent and Intervention Agent to Agent Engine (see PRD section 11) — resolve MCP/A2A compatibility issues that blocked the initial attempt

## Vague future things (don't plan yet)

- Lab instructions / student guide (how to deconstruct and rebuild)
- Scaffolding for early lab sections vs. open-ended final section
- README.md for the repo

## Resolved questions

- **Build order for agents**: Dev order: Data Agent first (simpler, proves BQ MCP on Cloud Run), then Orchestrator wired to Data Agent only (proves A2A client → server flow, deploys to Agent Engine), then Intervention Agent (Cloud Run), then wire Intervention into Orchestrator. This incremental approach validates each A2A hop before adding complexity. Lab order may differ — students may do AI Applications ToS + Vertex AI Search setup early to allow indexing time.
- **Local dev vs. cloud-first**: Develop and test locally with ADK first, then deploy (to Cloud Run for Data/Intervention agents, to Agent Engine for Orchestrator).
- **Agent Engine vs Cloud Run for Data/Intervention agents**: Initially planned all agents on Agent Engine. MCP and A2A agent deployment to Agent Engine hit compatibility issues. Pivot: deploy Data Agent and Intervention Agent to Cloud Run as A2A services, Orchestrator to Agent Engine. Cloud Run approach is working and proven with the Data Agent. Will revisit Agent Engine deployment for all agents later (PRD section 11).
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
- `gsutil iam ch allUsers:objectViewer` for the interventions bucket may hit org policy constraints in locked-down lab environments — signed download URLs from the GCS MCP server are the preferred fallback
- GCS signed URL generation requires `iam.serviceAccounts.signBlob` on the `gcs-mcp-sa@` service account. Grant it with: `gcloud iam service-accounts add-iam-policy-binding gcs-mcp-sa@$PROJECT_ID.iam.gserviceaccount.com --member="serviceAccount:gcs-mcp-sa@$PROJECT_ID.iam.gserviceaccount.com" --role="roles/iam.serviceAccountTokenCreator"` — this is a self-grant so the SA can sign its own URLs on Cloud Run
- Reference docs use fictional but internally consistent product details (firmware versions, DSCP values, bandwidth thresholds, quality score scales) — these must stay consistent with the synthetic data baselines in PRD 3.4 (e.g., healthy video_quality_score mean of 4.2 matches the "Good" threshold in the troubleshooting guides)
- `generate_data.py` uses `WRITE_TRUNCATE` disposition — re-running replaces all data rather than appending duplicates. This is the right default for idempotent lab scripts but means you can't incrementally add data
- BrightPath (declining usage) decline curve is `[1.0, 1.0, 1.0, 0.85, 0.65, 0.45, 0.35]` across 7 weeks — applied to logins, calls, and calendar events. Week-over-week decline should be clearly visible in SQL `GROUP BY EXTRACT(WEEK FROM ...)` queries
- Pinnacle (low login adoption) generates emails for only ~25% of licensed users — the `COUNT(DISTINCT user_email) / licensed_users` signal depends on this, not just lower login frequency
- `customers` table uses a `REPEATED RECORD` for interactions (BigQuery nested/repeated fields) — the Data Agent's system prompt must document this nested structure so the LLM generates correct `UNNEST()` SQL
- BigQuery MCP endpoint requires a separate enablement (`gcloud beta services mcp enable bigquery.googleapis.com`) beyond the standard `gcloud services enable bigquery.googleapis.com`. Without it, `tools/list` succeeds but `tools/call` returns 403. Added to `setup.sh`
- Gemini 3 models require `location='global'` — incompatible with Agent Engine which needs a regional location (e.g., `us-central1`). Implemented workaround in Data Agent: `Gemini3(Gemini)` subclass that overrides `api_client` to force `location='global'`. Same workaround applies to Intervention Agent on Cloud Run
- ADC user credentials ignore the `scopes` parameter in `google.auth.default()` — the token carries whatever scopes were granted at `gcloud auth application-default login` time. Use `cloud-platform` scope (the default) rather than narrow scopes like `bigquery`
- Cloud Run A2A agents require `--no-allow-unauthenticated` — the Orchestrator (on Agent Engine) authenticates via OIDC identity tokens. The orchestrator's SA needs `roles/run.invoker` on each Cloud Run agent service
- Agent Engine → Cloud Run A2A auth: the Orchestrator's SA (either the custom `cymbal-agent@` or the AI Platform Reasoning Engine service agent) must be able to generate identity tokens for the Cloud Run service URLs