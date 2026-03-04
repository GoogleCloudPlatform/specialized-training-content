# Cymbal Meet Customer Engagement Agent System

Multi-agent system on Google Cloud that identifies underengaged Cymbal Meet customers and generates tailored intervention PDFs. Built with ADK, Agent Engine, A2A, and MCP.

## What This Solution Does

**Cymbal Meet** is a fictional enterprise videoconferencing company that sells conference room devices and SaaS software licenses. Customer underutilization is a churn risk — when customers don't fully adopt the product, they're less likely to renew.

This system automates the identification and remediation of engagement problems. A user (e.g., a customer success manager) asks a natural language question like *"Create interventions for customers that have an engagement shortfall in scheduled meeting events."* The system then:

1. Queries BigQuery for customer engagement metrics to find at-risk customers
2. Retrieves relevant best practices and troubleshooting content via Vertex AI Search (RAG)
3. Generates branded, customer-specific intervention PDFs
4. Uploads PDFs to GCS and returns download links

The solution is also the basis for a hands-on lab where students learn to build agentic systems on Google Cloud.

## Architecture

![Agent Architecture](agent_arch.png)


### Agent Roles

| Agent                        | Deployment      | Role                                                                                                                                      |
| ---------------------------- | --------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| **Improve Engagement Agent** | Agent Engine    | User-facing coordinator. Interprets requests, delegates to sub-agents, presents results. Published to Gemini Enterprise.                  |
| **Data Agent**               | Cloud Run (A2A) | Domain expert on customer data. Translates natural language questions into SQL and executes against BigQuery via the BigQuery MCP server. |
| **Intervention Agent**       | Cloud Run (A2A) | Builds branded PDF intervention documents using RAG content from Vertex AI Search, then uploads to GCS via the GCS MCP server.            |

### How Agents Connect

Agents communicate via the **A2A (Agent-to-Agent) protocol** — an open standard for inter-agent communication. Cloud Run agents serve an agent card at `/.well-known/agent.json` describing their capabilities. The Improve Engagement Agent uses ADK's `RemoteA2aAgent` to call sub-agents, authenticating with OIDC identity tokens for Cloud Run endpoints.

### External System Integration

| System           | Protocol                                 | Agent              | Purpose                                               |
| ---------------- | ---------------------------------------- | ------------------ | ----------------------------------------------------- |
| BigQuery         | MCP (Google's official BQ MCP server)    | Data Agent         | SQL execution, schema discovery                       |
| GCS              | MCP (custom FastMCP server on Cloud Run) | Intervention Agent | Signed URL generation for PDF upload/download         |
| Vertex AI Search | ADK `VertexAiSearchTool`                 | Intervention Agent | RAG retrieval of troubleshooting & best practice docs |

## Calling the A2A Agents

Cloud Run A2A agents require OIDC authentication. Here's an example using `curl`:

```bash
# Get an identity token
TOKEN=$(gcloud auth print-identity-token)

# Send a message to the Data Agent
curl -X POST https://data-agent-<PROJECT_NUMBER>.us-central1.run.app/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "message/send",
    "params": {
      "message": {
        "role": "user",
        "parts": [{"type": "text", "text": "Which customers have the lowest login rates?"}]
      }
    },
    "id": "1"
  }'
```

For interactive testing, use the **A2A Inspector** — see [test/README.md](test/README.md) for setup instructions.

## End-to-End Flow

1. **User prompt** (via Gemini Enterprise): *"Create interventions for customers with an engagement shortfall in scheduled meeting events"*
2. **Improve Engagement Agent** formulates a data question and sends it to the **Data Agent** via A2A
3. **Data Agent** translates to SQL, executes against BigQuery via MCP, returns structured results (customers with low meeting engagement)
4. **Improve Engagement Agent** identifies at-risk customers and sends customer context to the **Intervention Agent** via A2A
5. **Intervention Agent** queries Vertex AI Search for relevant content, generates a branded PDF, uploads to GCS via MCP, returns the download link
6. **Improve Engagement Agent** presents a summary with intervention links and recommended next steps

## Directory Structure

```
atf_cloud_interactive/
├── PLAN.md                             # Technical roadmap
├── PRD.md                              # Product requirements
├── DOC_UPDATE_PLAN.md                  # Documentation update checklist
├── .gitignore
├── agents/
│   ├── requirements.txt                # Shared Python deps (all agents)
│   ├── deploy_improve_agent_to_agent_engine.sh
│   ├── data_agent/
│   ├── intervention_agent/
│   └── improve_engagement_agent/
├── reference_docs/
│   ├── markdown/                       # Source docs (5 fictional Cymbal Meet docs)
│   └── pdf/                            # Pre-generated PDFs (uploaded to GCS)
├── setup/
├── test/                               # Test & debug utilities
└── archive/                            # Superseded file versions (reference only)
```

## Detailed Documentation

### Agent-specific READMEs

Each agent has its own README with setup, local development, deployment, and testing instructions:

- [Data Agent README](agents/data_agent/README.md) — Cloud Run deployment, A2A testing
- [Intervention Agent README](agents/intervention_agent/README.md) — WeasyPrint setup, Cloud Run deployment, A2A testing
- [Improve Engagement Agent README](agents/improve_engagement_agent/README.md) — Agent Engine deployment, `adk web` local dev

### Infrastructure & Testing

- [Setup README](setup/README.md) — Infrastructure provisioning (APIs, service accounts, IAM, GCS, BigQuery, Vertex AI Search, GCS MCP server)
- [GCS MCP Server README](setup/gcs-mcp-server/README.md) — Custom MCP server for GCS operations
- [Test README](test/README.md) — Ad-hoc test scripts, A2A Inspector usage, MCP Inspector usage
