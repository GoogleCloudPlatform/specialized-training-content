# PRD - Cymbal Meet Customer Engagement Agent System

This document serves as the product requirements for building an agentic solution that demonstrates developing and running agents with ADK, Agent Engine, A2A, and MCP on Google Cloud. It also serves as persistent memory for Claude Code during the build process.

## 1. Overview

### 1.1 Purpose

Build a multi-agent system that automatically identifies Cymbal Meet customers who are underengaged with the product or experiencing product issues, then defines and executes tailored interventions for each customer.

### 1.2 Context

**Cymbal Meet** is a fictional enterprise videoconferencing company. They sell:
- Physical conference room devices ("boxes") installed in meeting rooms
- SaaS software licenses for individual users (desktop, mobile, web clients)

Customers span Enterprise, Mid-Market, and SMB segments. Customer underutilization is a churn risk — when customers don't fully adopt the product, they're less likely to renew.

### 1.3 Lab Use

This solution is the basis for a hands-on lab where students learn to build agentic systems on Google Cloud. The lab will:
1. Present the completed solution
2. Deconstruct it into buildable pieces
3. Have students rebuild it step-by-step (with scaffolding in early sections)
4. In the final section, ask students to build without step-by-step instructions (providing the solution for reference)

### 1.4 Learning Objectives

Students should get equal hands-on experience with:
- **ADK agent development** — building agents, defining tools, composing multi-agent systems
- **Agent Engine deployment** — deploying agents, managing lifecycle, publishing to Gemini Enterprise
- **A2A + MCP protocols** — inter-agent communication via A2A, tool integration via MCP

## 2. Architecture

### 2.1 System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Gemini Enterprise                        │
│                  (End-user interface)                         │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│              Orchestrator Agent                               │
│           (Agent Engine / ADK)                                │
│                                                              │
│  - Receives natural language requests from users              │
│  - Composes SQL queries for data retrieval                    │
│  - Coordinates Data Agent and Intervention Agent via A2A      │
│  - Presents results and intervention links to user            │
└────────┬──────────────────────────────┬─────────────────────┘
         │ A2A                          │ A2A
┌────────▼────────────┐     ┌──────────▼──────────────────────┐
│    Data Agent        │     │    Intervention Agent            │
│ (Agent Engine / ADK) │     │ (Agent Engine / ADK)             │
│                      │     │                                  │
│ - BigQuery interface │     │ - Reads reference docs via       │
│   via MCP            │     │   Vertex AI Search (RAG)         │
│ - Executes queries   │     │ - Generates intervention PDFs    │
│ - Returns structured │     │   (WeasyPrint + Jinja2)          │
│   results            │     │ - Writes PDFs to GCS bucket      │
│                      │     │ - Returns public links           │
└────────┬────────────┘     └──────────┬──────────────────────┘
         │ MCP                         │
┌────────▼────────────┐     ┌──────────▼──────────────────────┐
│     BigQuery         │     │  GCS Bucket     │ Vertex AI     │
│  (customer data)     │     │  (PDFs + refs)  │ Search (RAG)  │
└─────────────────────┘     └─────────────────────────────────┘
```

### 2.2 Agent Descriptions

#### Orchestrator Agent
- **Framework:** ADK
- **Deployment:** Agent Engine, published to Gemini Enterprise
- **Role:** User-facing agent that interprets natural language requests about customer engagement, coordinates the other agents, and presents results
- **Example prompts:**
  - "Create interventions for customers that have an engagement shortfall in scheduled meeting events"
  - "Create interventions for customers that are having low performance on conference room devices"
  - "Which customers have the lowest login rates relative to their licensed users?"
- **Workflow:**
  1. Interpret user request and compose an appropriate SQL query
  2. Send query to Data Agent via A2A
  3. Receive structured results
  4. For each customer needing intervention, send customer context to Intervention Agent via A2A
  5. Collect intervention PDF links
  6. Present summary with links and recommended next steps to the user

#### Data Agent
- **Framework:** ADK
- **Deployment:** Agent Engine
- **Exposed via:** A2A (callable by Orchestrator)
- **Role:** Interface to BigQuery data. Accepts natural language questions or specific SQL queries, executes them, and returns structured results.
- **Tools:** Google's official BigQuery MCP server
- **Capabilities:**
  - Execute SQL queries against Cymbal Meet BigQuery tables
  - Answer natural language questions about customer data
  - Return results in structured format suitable for downstream processing

#### Intervention Agent
- **Framework:** ADK
- **Deployment:** Agent Engine
- **Exposed via:** A2A (callable by Orchestrator)
- **Role:** Builds customized intervention documents for specific customers based on their issues and reference content.
- **Tools:**
  - Vertex AI Search — retrieves relevant product docs, troubleshooting guides, and best practice content
  - WeasyPrint + Jinja2 — generates styled PDF documents
  - GCS client — writes PDFs to customer-specific folders and generates public links
- **Workflow:**
  1. Receive customer context and issue description from Orchestrator
  2. Query Vertex AI Search for relevant reference content (troubleshooting, best practices, templates)
  3. Synthesize a tailored intervention document
  4. Render as PDF using HTML template + WeasyPrint
  5. Upload to GCS bucket at `gs://{bucket}/{customer_id}/{intervention_id}.pdf`
  6. Enable public read access on the object
  7. Return the public URL

## 3. BigQuery Data Model

### 3.1 Dataset

- **Dataset name:** `cymbal_meet`
- **Location:** US (multi-region)
- **Data volume:** ~25 customers with proportional data across all tables

### 3.2 Tables

#### `customers`

| Column | Type | Description |
|---|---|---|
| customer_id | STRING | Unique identifier |
| company_name | STRING | Company name |
| segment | STRING | `Enterprise` / `Mid-Market` / `SMB` |
| licensed_users | INT64 | Number of licensed Cymbal Meet seats |
| conference_rooms | INT64 | Number of rooms with Cymbal Meet devices |
| annual_contract_value | FLOAT64 | ACV in dollars |
| contract_start_date | DATE | When the contract began |
| csm_name | STRING | Assigned customer success manager |
| interactions | ARRAY\<STRUCT\<interaction_date DATE, type STRING, contact_name STRING, note STRING\>\> | CRM interaction history |

**Interaction types:** `Support`, `Health Check`, `Maintenance`, `Renewal Discussion`, `Executive Review`, `CSM`

**Example interaction notes:**
- "Audio lag issues reported in Room 302, escalated to engineering"
- "Discussed seat expansion for Q2, customer interested in 50 additional licenses"
- "Quarterly business review with CIO — satisfaction high but adoption uneven across departments"
- "Firmware update completed on 12 conference room devices"
- "Low adoption flagged in marketing department — recommended enablement session"

#### `logins`

| Column | Type | Description |
|---|---|---|
| login_id | STRING | Unique identifier |
| customer_id | STRING | FK to customers |
| user_email | STRING | User who logged in |
| login_timestamp | TIMESTAMP | When the login occurred |
| platform | STRING | `desktop` / `mobile` / `web` |

#### `calendar_events`

| Column | Type | Description |
|---|---|---|
| event_id | STRING | Unique identifier |
| customer_id | STRING | FK to customers |
| organizer_email | STRING | Who scheduled the event |
| event_date | DATE | Date of the event |
| start_time | TIMESTAMP | Event start time |
| end_time | TIMESTAMP | Event end time |
| invited_count | INT64 | Number of invitees |
| cal_platform | STRING | `google_calendar` / `outlook` / `other` |

#### `device_telemetry`

| Column | Type | Description |
|---|---|---|
| telemetry_id | STRING | Unique identifier |
| customer_id | STRING | FK to customers |
| device_id | STRING | Specific device identifier |
| room_name | STRING | Conference room name |
| timestamp | TIMESTAMP | When the reading was taken |
| cpu_usage_pct | FLOAT64 | CPU usage percentage |
| memory_usage_pct | FLOAT64 | Memory usage percentage |
| network_latency_ms | FLOAT64 | Network latency in milliseconds |
| packet_loss_pct | FLOAT64 | Packet loss percentage |
| video_quality_score | FLOAT64 | Quality score (1.0–5.0) |

#### `calls`

| Column | Type | Description |
|---|---|---|
| call_id | STRING | Unique identifier |
| customer_id | STRING | FK to customers |
| initiator_email | STRING | Who started the call |
| start_timestamp | TIMESTAMP | Call start time |
| duration_minutes | INT64 | Actual call length |
| participant_count | INT64 | Number of participants |
| call_type | STRING | `scheduled` / `ad_hoc` |
| avg_quality_score | FLOAT64 | Average video quality (1.0–5.0) |
| drop_count | INT64 | Number of drops during call |

### 3.3 Engagement Problem Signals

The data should be generated such that a subset of customers (~7-10) exhibit clear engagement problems detectable via SQL queries:

| Problem Type | Signal in Data |
|---|---|
| Low login adoption | Login count / licensed_users ratio significantly below peers in same segment |
| Meeting underutilization | Few calendar events relative to licensed users; low invited counts |
| Device performance issues | High packet_loss_pct, high network_latency_ms, low video_quality_score in telemetry |
| Call quality problems | Low avg_quality_score, high drop_count in calls |
| Declining usage | Login or call volume trending downward over recent weeks |
| Low ad-hoc adoption | Very few `ad_hoc` calls — customers only use scheduled meetings, not adopting casual use |

## 4. Reference Content for Interventions

### 4.1 Content Types

Create a small set of fictional Cymbal Meet documents that the Intervention Agent retrieves via Vertex AI Search:

1. **Product Best Practices Guide** — How to drive adoption across an organization (executive sponsorship, department champions, training programs, gamification)
2. **Troubleshooting Guide: Device Performance** — Common device issues and solutions (network configuration, firmware updates, hardware replacement criteria)
3. **Troubleshooting Guide: Call Quality** — Diagnosing and fixing call quality issues (bandwidth requirements, QoS settings, client configuration)
4. **Admin Guide: User Onboarding** — Step-by-step onboarding best practices for new Cymbal Meet users
5. **Intervention Templates** — Template structures for different intervention types (adoption plan, technical remediation plan, executive briefing)

### 4.2 Storage and Retrieval

- Reference documents stored as files in a GCS bucket
- Indexed by a Vertex AI Search datastore and search app
- Intervention Agent queries the search app to retrieve relevant content based on the customer's specific issues

### 4.3 Vertex AI Search Setup

- **Datastore type:** Unstructured documents
- **Data source:** GCS bucket containing reference docs
- **Search app:** Connected to the datastore, used by the Intervention Agent as a tool
- Setup script should automate: bucket creation, document upload, datastore creation, document ingestion, search app creation

## 5. Intervention PDF Generation

### 5.1 Approach

- **Templating:** Jinja2 HTML templates with CSS styling
- **Rendering:** WeasyPrint converts styled HTML to PDF
- **Storage:** Upload to GCS with public read access enabled

### 5.2 PDF Content Structure

Each intervention PDF should include:
- **Header:** Cymbal Meet logo/branding, intervention date, customer name
- **Executive Summary:** Brief description of the identified issue
- **Data Snapshot:** Key metrics that triggered the intervention (e.g., login rate, quality scores)
- **Recommended Actions:** Numbered list of specific steps tailored to the customer's situation, informed by reference content
- **Resources:** Links to relevant Cymbal Meet documentation
- **CSM Contact:** Name and next steps for follow-up

### 5.3 GCS Organization

```
gs://{project-id}-cymbal-meet-interventions/
  └── {customer_id}/
      └── {YYYY-MM-DD}_{intervention_type}_{intervention_id}.pdf
```

## 6. GCP Infrastructure and Authentication

### 6.1 Required GCP Services

| Service | Purpose |
|---|---|
| Agent Engine (Vertex AI) | Agent deployment and management |
| BigQuery | Customer data storage and querying |
| Cloud Storage (GCS) | Reference docs, intervention PDFs |
| Vertex AI Search | RAG over reference documents |
| IAM | Service accounts and permissions |

### 6.2 Service Account

A single service account for the agent system with the following roles:

| Role | Purpose |
|---|---|
| `roles/bigquery.dataViewer` | Read BigQuery tables |
| `roles/bigquery.jobUser` | Execute BigQuery queries |
| `roles/storage.objectAdmin` | Read/write GCS objects (reference docs + PDFs) |
| `roles/aiplatform.user` | Deploy and manage Agent Engine agents |
| `roles/discoveryengine.editor` | Create and query Vertex AI Search datastores |

### 6.3 Student Environment

- Each student gets their own GCP project
- Setup script provisions all required resources within the project
- All resource names are parameterized by project ID to avoid collisions

## 7. Technology Stack

| Component | Technology | Version |
|---|---|---|
| Agent framework | Google ADK | Latest stable |
| Inter-agent protocol | A2A (Google) | Latest stable |
| BigQuery integration | Google's official BigQuery MCP server | Latest stable |
| Language | Python | 3.11+ |
| PDF templating | Jinja2 | Latest stable |
| PDF rendering | WeasyPrint | Latest stable |
| RAG retrieval | Vertex AI Search | Latest |
| Deployment | Agent Engine (Vertex AI) | Latest |
| End-user interface | Gemini Enterprise | Latest |

## 8. Directory Structure

```
atf_cloud_interactive/
├── PRD.md                          # This file
├── PLAN.md                         # Build plan and progress tracking
├── setup/
│   ├── setup.sh                    # Main setup script (orchestrates everything)
│   ├── create_bq_tables.py         # Creates BigQuery dataset and tables
│   ├── generate_data.py            # Generates synthetic data and loads into BQ
│   ├── create_gcs_buckets.py       # Creates GCS buckets for refs and interventions
│   ├── upload_reference_docs.py    # Uploads reference docs to GCS
│   └── create_search_app.py        # Creates Vertex AI Search datastore and app
├── reference_docs/
│   ├── best_practices_guide.md     # Product adoption best practices
│   ├── troubleshooting_devices.md  # Device performance troubleshooting
│   ├── troubleshooting_calls.md    # Call quality troubleshooting
│   ├── admin_onboarding_guide.md   # User onboarding guide
│   └── intervention_templates.md   # Intervention document templates
├── agents/
│   ├── orchestrator/
│   │   ├── agent.py                # Orchestrator agent definition
│   │   └── prompt.py               # System prompt and instructions
│   ├── data_agent/
│   │   ├── agent.py                # Data agent definition
│   │   ├── prompt.py               # System prompt and instructions
│   │   └── mcp_config.json         # BigQuery MCP server configuration
│   └── intervention_agent/
│       ├── agent.py                # Intervention agent definition
│       ├── prompt.py               # System prompt and instructions
│       ├── pdf_generator.py        # WeasyPrint + Jinja2 PDF generation
│       └── templates/
│           └── intervention.html   # HTML/CSS template for intervention PDFs
├── deploy/
│   ├── deploy_agents.py            # Deploys all agents to Agent Engine
│   └── publish_to_gemini.py        # Publishes orchestrator to Gemini Enterprise
├── requirements.txt                # Python dependencies
└── README.md                       # Setup and usage instructions
```

## 9. Example End-to-End Flow

**User prompt in Gemini Enterprise:**
> "Create interventions for customers that have an engagement shortfall in scheduled meeting events"

**Step 1 — Orchestrator interprets and queries:**
- Orchestrator composes a SQL query to find customers with low calendar event counts relative to their licensed users
- Sends query to Data Agent via A2A

**Step 2 — Data Agent executes:**
- Data Agent receives the query
- Executes against BigQuery via MCP
- Returns structured results: list of customers with low meeting engagement, their metrics, and context

**Step 3 — Orchestrator processes results:**
- Identifies 4 customers needing intervention
- For each customer, prepares a context payload (customer info, specific metrics, issue type)
- Sends each to Intervention Agent via A2A

**Step 4 — Intervention Agent creates documents:**
- For each customer:
  - Queries Vertex AI Search for relevant best practices and troubleshooting content
  - Generates a tailored intervention document
  - Renders to PDF via WeasyPrint
  - Uploads to GCS at `gs://{bucket}/{customer_id}/...`
  - Returns the public URL

**Step 5 — Orchestrator presents results:**
- Collects all intervention links
- Presents to the user:
  ```
  Interventions created for 4 customers with meeting engagement shortfalls:

  1. Nexus Tech (Enterprise) — Login rate at 34% of licensed users
     Intervention: https://storage.googleapis.com/.../nexus_tech/2026-02-25_adoption_abc123.pdf

  2. Summit Peak (SMB) — Only 12 calendar events in past 30 days (expected: 80+)
     Intervention: https://storage.googleapis.com/.../summit_peak/2026-02-25_adoption_def456.pdf

  ...

  Recommended next step: Review each intervention and share with the assigned CSM
  for customer outreach.
  ```
