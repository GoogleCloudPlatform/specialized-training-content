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
- Synthetic data is hand-designed profiles + programmatic generation — the 25 customers and 5 problem profiles are hand-specified in PRD 3.4, but the ~422K data rows are generated via seeded numpy RNG (`generate_data.py`). This gives deterministic, reproducible data with obvious outliers detectable via simple SQL GROUP BY queries

## Completed

- [x] Setup scripts — infrastructure provisioning (APIs, service accounts, IAM, buckets)
  - `setup/setup.sh` — enables 12 APIs, creates 2 SAs with IAM roles, creates 3 GCS buckets, runs validation checks
  - Parameterized by `$PROJECT_ID` (falls back to gcloud config), idempotent, includes next-steps guidance
- [x] GCS MCP server — custom Python FastMCP server on Cloud Run
  - `setup/gcs-mcp-server/server.py` — ~90-line FastMCP server wrapping `google-cloud-storage` with 3 tools: `list_objects`, `read_object`, `write_object` (supports base64 for PDFs)
  - Deploys natively to Cloud Run with Streamable HTTP transport (endpoint at `/mcp`) — no bridge layer
  - `setup/deploy_gcs_mcp.sh` — builds via Cloud Build, deploys to Cloud Run with `gcs-mcp-sa@`, grants `cymbal-agent@` invoker access, prints the MCP endpoint URL
- [x] Reference docs — 5 fictional Cymbal Meet documents for Vertex AI Search RAG
  - `reference_docs/product_best_practices_guide.md` — adoption strategy, executive sponsorship, champions program, training, gamification
  - `reference_docs/troubleshooting_device_performance.md` — device telemetry baselines, network/QoS issues, firmware, hardware replacement
  - `reference_docs/troubleshooting_call_quality.md` — call quality scoring, audio/video issues, client-specific troubleshooting, IT security config impacts
  - `reference_docs/admin_guide_user_onboarding.md` — onboarding timelines (standard, accelerated, acquired workforce), training tiers, adoption metrics
  - `reference_docs/intervention_templates.md` — 5 template structures (adoption plan, technical remediation, executive briefing, re-engagement, onboarding acceleration)

## In progress

_(nothing yet)_

## Upcoming (ordered)
- [ ] BigQuery data layer — dataset, tables, synthetic data generation (~25 customers)
- [ ] Vertex AI Search — datastore creation, doc ingestion, indexing
- [ ] Data Agent — ADK agent with BigQuery MCP, NL-to-SQL, system prompt with full schema
- [ ] Intervention Agent — RAG retrieval, PDF generation, GCS write via MCP
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

## Open questions


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