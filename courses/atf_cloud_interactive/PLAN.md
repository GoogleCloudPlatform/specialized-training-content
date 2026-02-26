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
- Reference docs are markdown files in `reference_docs/` — Vertex AI Search ingests unstructured docs (markdown, PDF, HTML) so no conversion step needed before upload to GCS
- Reference doc content is deliberately aligned to the 5 problem customer profiles in PRD 3.4 — each problem customer's root cause maps to specific retrievable sections across the docs, so the Intervention Agent's RAG queries will return actionable content
- Synthetic data is hand-designed profiles + programmatic generation — the 25 customers and 5 problem profiles are hand-specified in PRD 3.4, but the ~3.6M data rows (dominated by device telemetry) are generated via seeded numpy RNG (`generate_data.py`). This gives deterministic, reproducible data with obvious outliers detectable via simple SQL GROUP BY queries
- Device telemetry is 1 reading/device every 5 minutes during business hours (8am–6pm weekdays) — ~3.1M rows across 746 devices × 120 readings/day × 35 weekdays
- Data gen loads via in-memory JSONL → `load_table_from_file` with `WRITE_TRUNCATE` — idempotent, no temp files on disk. Telemetry table (~3M rows) is the bottleneck; logins/calls/events are fast
- `create_bq_tables.py` and `generate_data.py` are separate scripts — schema creation is fast/idempotent, data gen is slow and benefits from `--dry-run` for validation without a GCP project

## Key files

### Setup & infrastructure
- `setup/setup.sh` — infra provisioning (APIs, SAs, IAM, buckets)
- `setup/deploy_gcs_mcp.sh` — builds + deploys GCS MCP to Cloud Run

### BigQuery data layer
- `setup/create_bq_tables.py` — creates `cymbal_meet` dataset + 5 tables (idempotent)
- `setup/generate_data.py` — deterministic synthetic data gen (~3.6M rows), loads via JSONL. Supports `--dry-run`

### GCS MCP server
- `setup/gcs-mcp-server/server.py` — FastMCP server (list/read/write)

### Reference docs & search
- `reference_docs/*.md` — 5 Cymbal Meet docs for RAG
- `setup/upload_reference_docs.py` — uploads ref docs to GCS
- `setup/create_search_app.py` — creates Vertex AI Search datastore, imports + indexes docs

## Completed

- [x] Setup scripts — infra provisioning (APIs, 2 service accounts, IAM, 3 buckets)
- [x] GCS MCP server — custom FastMCP on Cloud Run with Streamable HTTP (`/mcp`)
- [x] Reference docs — 5 fictional Cymbal Meet docs aligned to PRD 3.4 problem profiles
- [x] Vertex AI Search — datastore creation, GCS import, indexing with polling
- [x] BigQuery data layer — `create_bq_tables.py` (dataset + 5 tables) + `generate_data.py` (seeded numpy RNG, ~3.6M rows, 5 problem profiles with obvious outliers, `--dry-run` support)

## Tasks — Data Agent Implementation

### Step 1: Create agent directory structure
- [ ] Create `agents/data_agent/__init__.py` — standard ADK boilerplate (`from . import agent`)
- [ ] Create `agents/data_agent/agent.py` — main agent definition with `root_agent`
- [ ] Create `agents/requirements.txt` — shared Python dependencies for all agents (`google-adk`, `google-auth`, `google-cloud-bigquery`)

### Step 2: Configure McpToolset for BigQuery MCP endpoint
- [ ] Set up `McpToolset` with `StreamableHTTPConnectionParams` pointing to `https://bigquery.googleapis.com/mcp`
- [ ] Authenticate via ADC: `google.auth.default(scopes=["https://www.googleapis.com/auth/bigquery"])` → `credentials.refresh()` → pass Bearer token in headers
- [ ] Pattern follows the [ADK BigQuery MCP sample](https://github.com/google/adk-python/tree/main/contributing/samples/bigquery_mcp): token obtained at agent module load time; for long sessions, restart the dev server

### Step 3: Write the system prompt
Per PRD 5.1, the Data Agent discovers schema at runtime (not hardcoded). The system prompt instructs the agent how to discover and query, not what the schema is:
- [ ] **Identity & scope**: "You are the Cymbal Meet data domain expert. You accept natural language questions about customer engagement and translate them into SQL."
- [ ] **Target dataset**: parameterized as `{PROJECT_ID}.cymbal_meet`
- [ ] **Discovery protocol** (lazy, on-demand):
  1. List tables: `SELECT table_name FROM \`{PROJECT_ID}.cymbal_meet.INFORMATION_SCHEMA.TABLES\``
  2. Inspect columns: `SELECT column_name, data_type, is_nullable, description FROM \`{PROJECT_ID}.cymbal_meet.INFORMATION_SCHEMA.COLUMNS\` WHERE table_name = '{table}'`
  3. Sample data: `SELECT * FROM \`{PROJECT_ID}.cymbal_meet.{table}\` LIMIT 5`
- [ ] **Nested field handling**: when INFORMATION_SCHEMA shows a column with `data_type = 'RECORD'` and `mode = 'REPEATED'`, instruct the agent to use `UNNEST()` (specifically relevant for `customers.interactions`)
- [ ] **Output format**: structured results with clear headers, suitable for downstream agents
- [ ] **Read-only constraint**: only SELECT queries, never INSERT/UPDATE/DELETE
- [ ] **Conversational memory**: schema discovered earlier in the conversation is already in context — reuse it rather than re-querying INFORMATION_SCHEMA

### Step 4: Define root_agent
- [ ] Model: `gemini-2.5-flash-preview`
- [ ] Name: `data_agent`
- [ ] Description (for A2A discoverability): "Cymbal Meet data domain expert. Accepts natural language questions about customer engagement, translates to SQL, executes via BigQuery, returns structured results."
- [ ] Instruction: the system prompt from Step 3
- [ ] Tools: `[bigquery_mcp_toolset]`

### Step 5: Add environment configuration
- [ ] Set required env vars in agent.py: `GOOGLE_CLOUD_PROJECT` (from env or `gcloud config`), `GOOGLE_CLOUD_LOCATION=us-central1`, `GOOGLE_GENAI_USE_VERTEXAI=True`
- [ ] Follow project convention: parameterized by `$PROJECT_ID` env var with `gcloud config get-value project` fallback

### Step 6: Test locally with ADK dev server
- [ ] Run `adk web agents/data_agent` from the course root
- [ ] Smoke test: "What tables are in the cymbal_meet dataset?" → should trigger INFORMATION_SCHEMA discovery and list 5 tables
- [ ] Query test: "How many customers are there and what segments are they in?" → should query customers table
- [ ] Complex query test: "Which customer has the lowest login rate relative to their licensed users?" → should detect Pinnacle Financial Group

### Step 7: Validate against all 5 problem customer profiles
Each problem customer should be detectable via natural language questions:
- [ ] **Pinnacle Financial** (low login adoption): "Which customers have fewer than 30% of licensed users logging in?" → `COUNT(DISTINCT user_email) / licensed_users` ≈ 0.25
- [ ] **Quantum Dynamics** (low ad-hoc + quality): "Which customers have almost no ad-hoc calls and poor call quality?" → ad-hoc ratio ~3%, avg quality ~2.8
- [ ] **Verdant Health** (meeting underutilization): "Which customers have normal login rates but very few calendar events?" → events/user far below segment avg
- [ ] **Coastal Logistics** (device issues): "Which customers have device telemetry showing poor performance across all rooms?" → packet loss ~4%, latency ~95ms, quality ~2.2
- [ ] **BrightPath Education** (declining usage): "Which customers show a declining trend in usage over the past 7 weeks?" → >50% drop weeks 1-3 → 5-7

## Upcoming (ordered)
- [ ] Intervention Agent — RAG retrieval via Vertex AI Search, PDF generation (Jinja2 + WeasyPrint), GCS write via MCP
- [ ] Orchestrator Agent — coordinates Data + Intervention agents via A2A
- [ ] Deployment — all agents to Agent Engine, orchestrator published to Gemini Enterprise
- [ ] End-to-end validation — test the full flow from PRD section 9

## Vague future things (don't plan yet)

- Lab instructions / student guide (how to deconstruct and rebuild)
- Scaffolding for early lab sections vs. open-ended final section
- README.md for the repo

## Resolved questions

- **Build order for agents**: Dev order: Data Agent first (simpler, proves BQ MCP), then decide next. Lab order: Data Agent → Orchestrator → Intervention Agent. Students may do AI Applications ToS + Vertex AI Search setup early to allow indexing time.
- **Local dev vs. cloud-first**: Develop and test locally with ADK first, then deploy to Agent Engine.
- **VertexAiSearchTool constraint**: ADK v1.16.0+ supports `bypass_multi_tools_limit=True` parameter directly on `VertexAiSearchTool`. No sub-agent or custom wrapper needed — the tool lives directly on the Intervention Agent alongside PDF/GCS tools.
- **PDF template fidelity**: Demo-quality with branding.
- **Reference doc format for Vertex AI Search**: Keep as markdown. Vertex AI Search ingests unstructured markdown directly. Only revisit if retrieval quality is poor during testing.
- **Data gen deployment strategy**: `generate_data.py` produces deterministic output via seeded RNG. For lab deployment, pre-generate JSONL files and host in a shared GCS bucket so students load via `bq load` without needing Python/numpy locally. The script itself is for development and pre-generation.

## Open questions

- **Telemetry generation memory/time**: ~3.1M telemetry rows are generated in-memory before loading. Need to validate this doesn't OOM on constrained lab VMs. If it does, may need to batch by customer or stream rows directly.
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