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
- `VertexAiSearchTool` constraint: must be only tool on its agent, so Intervention Agent needs a sub-agent or custom tool wrapper for search

## Completed

_(nothing yet)_

## In progress

_(nothing yet)_

## Upcoming (ordered)

- [ ] Setup scripts — infrastructure provisioning (APIs, service accounts, IAM, buckets)
- [ ] BigQuery data layer — dataset, tables, synthetic data generation (~25 customers)
- [ ] Reference docs — 5 fictional Cymbal Meet documents (best practices, troubleshooting, onboarding, templates)
- [ ] Vertex AI Search — datastore creation, doc ingestion, indexing
- [ ] GCS MCP server — deploy `@google-cloud/storage-mcp` to Cloud Run
- [ ] Data Agent — ADK agent with BigQuery MCP, NL-to-SQL, system prompt with full schema
- [ ] Intervention Agent — RAG retrieval, PDF generation, GCS write via MCP
- [ ] Orchestrator Agent — coordinates Data + Intervention agents via A2A
- [ ] Deployment — all agents to Agent Engine, orchestrator published to Gemini Enterprise
- [ ] End-to-end validation — test the full flow from PRD section 9

## Vague future things (don't plan yet)

- Lab instructions / student guide (how to deconstruct and rebuild)
- Scaffolding for early lab sections vs. open-ended final section
- README.md for the repo

## Open questions

- **Target GCP project**: Are we building against a real project, or writing scripts that are project-agnostic (parameterized by `$PROJECT_ID`)?
- **Build order for agents**: Start with Data Agent (simpler, proves BQ MCP) or Intervention Agent (more moving parts, longer lead time for Vertex AI Search indexing)?
- **Local dev vs. cloud-first**: Do we develop/test agents locally with ADK before deploying to Agent Engine, or go straight to cloud?
- **Synthetic data strategy**: Hand-craft the ~25 customers to ensure clear engagement problem signals (section 3.3), or generate programmatically with controlled randomness?
- **VertexAiSearchTool constraint**: Use a sub-agent within Intervention Agent for search, or wrap Vertex AI Search as a custom tool via the Discovery Engine client library?
- **PDF template fidelity**: How polished do the intervention PDFs need to be for the lab? Functional with basic styling, or demo-quality with branding?

## Assumptions and gotchas

- PRD specifies ~25 customers with ~3-4 exhibiting clear engagement problems — data gen must be deliberate, not purely random
- Vertex AI Search indexing takes 5-30 minutes — start Phase 3 early in setup
- Cloud Run GCS MCP needs `ENABLE_DESTRUCTIVE_TOOLS=true` env var for write operations
- Intervention bucket needs public read access configured for PDF URLs to work
- Agent Engine staging bucket (`gs://$PROJECT_ID-agent-staging`) is required before any agent deployment
- The provisioning order in PRD section 7.2 has real dependency constraints — don't parallelize carelessly
- AI Applications console (gen-app-builder) requires manual ToS acceptance — can't be fully automated

## Next session

Decide the build order and resolve the open questions above. Then start on the first concrete task: setup scripts for Phase 1 (API enablement, service accounts, IAM roles, staging bucket).
