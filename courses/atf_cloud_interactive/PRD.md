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
│  - Delegates data questions to Data Agent via A2A             │
│  - Delegates intervention creation to Intervention Agent      │
│  - Presents results and intervention links to user            │
└────────┬──────────────────────────────┬─────────────────────┘
         │ A2A                          │ A2A
┌────────▼────────────┐     ┌──────────▼──────────────────────┐
│    Data Agent        │     │    Intervention Agent            │
│ (Agent Engine / ADK) │     │ (Agent Engine / ADK)             │
│                      │     │                                  │
│ - Accepts natural    │     │ - Reads reference docs via       │
│   language questions │     │   Vertex AI Search (RAG)         │
│ - Translates to SQL  │     │ - Generates intervention PDFs    │
│ - Executes via MCP   │     │   (WeasyPrint + Jinja2)          │
│ - Returns structured │     │ - Writes PDFs to GCS via MCP     │
│   results            │     │ - Returns public links           │
└────────┬────────────┘     └────────┬─────────┬──────────────┘
         │ MCP                       │ MCP     │
┌────────▼────────────┐     ┌────────▼───┐ ┌───▼──────────────┐
│     BigQuery         │     │ GCS MCP    │ │  Vertex AI       │
│  (customer data)     │     │ (Cloud Run)│ │  Search (RAG)    │
└─────────────────────┘     └────────┬───┘ └──────────────────┘
                                     │
                            ┌────────▼───────────────────────┐
                            │  GCS Buckets                    │
                            │  (PDFs + reference docs)        │
                            └────────────────────────────────┘
```

### 2.2 Agent Descriptions

#### Orchestrator Agent
- **Framework:** ADK
- **Deployment:** Agent Engine, published to Gemini Enterprise
- **Role:** User-facing agent that interprets natural language requests about customer engagement, coordinates the other agents, and presents results. The Orchestrator describes *what* data it needs — it does not compose SQL or know the BigQuery schema. It delegates data questions to the Data Agent and intervention creation to the Intervention Agent.
- **Example prompts:**
  - "Create interventions for customers that have an engagement shortfall in scheduled meeting events"
  - "Create interventions for customers that are having low performance on conference room devices"
  - "Which customers have the lowest login rates relative to their licensed users?"
- **Workflow:**
  1. Interpret user request and formulate a natural language data question
  2. Send the data question to Data Agent via A2A (e.g., "Which customers have significantly fewer calendar events per licensed user than their segment average?")
  3. Receive structured results
  4. For each customer needing intervention, send customer context to Intervention Agent via A2A
  5. Collect intervention PDF links
  6. Present summary with links and recommended next steps to the user

#### Data Agent
- **Framework:** ADK
- **Deployment:** Agent Engine
- **Exposed via:** A2A (callable by Orchestrator)
- **Role:** Domain expert on Cymbal Meet's data. Accepts natural language questions about customer engagement, translates them into SQL, executes queries, and returns structured results. The Data Agent owns all knowledge of the BigQuery schema — no other agent needs to understand table structures or write SQL.
- **Tools:** Google's official BigQuery MCP server
- **Capabilities:**
  - Interpret natural language data questions (e.g., "Which customers have low login rates relative to licensed users?")
  - Translate questions into appropriate SQL queries against the Cymbal Meet schema
  - Execute queries against BigQuery via MCP
  - Return results in structured format suitable for downstream processing
- **Model:** `gemini-3-flash-preview` via a `Gemini3(Gemini)` subclass that forces `location='global'` (required for Gemini 3 models, which are incompatible with Agent Engine's regional location setting)
- **Schema discovery:** The Data Agent does **not** have the schema hardcoded in its system prompt. Instead, it discovers schema at runtime using the BigQuery MCP server's built-in tools. This makes the agent generalizable — it can work against any dataset it is pointed at, not just the one it was built for.
- **Discovery approach — lazy, on-demand via MCP tools:**
  - `list_table_ids` — lists all tables in the target dataset
  - `get_table_info` — returns column names, types, modes (including REPEATED RECORD fields) for a specific table
  - `execute_sql` with `SELECT * FROM ... LIMIT 5` — samples live data when needed to understand real values before composing queries
  - The agent discovers tables on demand as questions require them, not all upfront.
- **Conversational memory:** Discovered schema is retained in the LLM's conversation context across turns. The system prompt instructs the agent to reuse previously discovered schema rather than re-calling `get_table_info`. This avoids redundant BigQuery MCP calls on follow-up questions.
- **System prompt contents:** Rather than schema details, the system prompt tells the agent:
  - The target project and dataset identifier (with env var fallback)
  - Which MCP tools to use for schema discovery (`list_table_ids`, `get_table_info`, `execute_sql`)
  - How to handle RECORD REPEATED fields with `UNNEST()` (critical for the `customers.interactions` nested structure)
  - Read-only constraint (SELECT only)
  - Output formatting guidelines (percentages, currency, segment benchmarks)

#### Intervention Agent
- **Framework:** ADK
- **Deployment:** Agent Engine
- **Exposed via:** A2A (callable by Orchestrator)
- **Role:** Builds customized intervention documents for specific customers based on their issues and reference content.
- **Tools:**
  - Vertex AI Search — retrieves relevant product docs, troubleshooting guides, and best practice content
  - WeasyPrint + Jinja2 — generates styled PDF documents
  - GCS MCP server (custom Python FastMCP server wrapping `google-cloud-storage`) — reads/writes objects in GCS via MCP. Deployed to Cloud Run as part of infrastructure setup. Provides tools: `list_objects`, `read_object`, `write_object`.
- **Workflow:**
  1. Receive customer context and issue description from Orchestrator
  2. Query Vertex AI Search for relevant reference content (troubleshooting, best practices, templates)
  3. Synthesize a tailored intervention document
  4. Render as PDF using HTML template + WeasyPrint
  5. Write PDF to GCS via the GCS MCP server at `gs://{bucket}/{customer_id}/{intervention_id}.pdf`
  6. Return the public URL

## 3. BigQuery Data Model

### 3.1 Dataset

- **Dataset name:** `cymbal_meet`
- **Location:** US (multi-region)
- **Data volume:** ~25 customers with proportional data across all tables

### 3.2 Tables

#### `customers`

| Column                | Type                                                                                    | Description                              |
| --------------------- | --------------------------------------------------------------------------------------- | ---------------------------------------- |
| customer_id           | STRING                                                                                  | Unique identifier                        |
| company_name          | STRING                                                                                  | Company name                             |
| segment               | STRING                                                                                  | `Enterprise` / `Mid-Market` / `SMB`      |
| licensed_users        | INT64                                                                                   | Number of licensed Cymbal Meet seats     |
| conference_rooms      | INT64                                                                                   | Number of rooms with Cymbal Meet devices |
| annual_contract_value | FLOAT64                                                                                 | ACV in dollars                           |
| contract_start_date   | DATE                                                                                    | When the contract began                  |
| csm_name              | STRING                                                                                  | Assigned customer success manager        |
| interactions          | ARRAY\<STRUCT\<interaction_date DATE, type STRING, contact_name STRING, note STRING\>\> | CRM interaction history                  |

**Interaction types:** `Support`, `Health Check`, `Maintenance`, `Renewal Discussion`, `Executive Review`, `CSM`

**Example interaction notes:**
- "Audio lag issues reported in Room 302, escalated to engineering"
- "Discussed seat expansion for Q2, customer interested in 50 additional licenses"
- "Quarterly business review with CIO — satisfaction high but adoption uneven across departments"
- "Firmware update completed on 12 conference room devices"
- "Low adoption flagged in marketing department — recommended enablement session"

#### `logins`

| Column          | Type      | Description                  |
| --------------- | --------- | ---------------------------- |
| login_id        | STRING    | Unique identifier            |
| customer_id     | STRING    | FK to customers              |
| user_email      | STRING    | User who logged in           |
| login_timestamp | TIMESTAMP | When the login occurred      |
| platform        | STRING    | `desktop` / `mobile` / `web` |

#### `calendar_events`

| Column          | Type      | Description                             |
| --------------- | --------- | --------------------------------------- |
| event_id        | STRING    | Unique identifier                       |
| customer_id     | STRING    | FK to customers                         |
| organizer_email | STRING    | Who scheduled the event                 |
| event_date      | DATE      | Date of the event                       |
| start_time      | TIMESTAMP | Event start time                        |
| end_time        | TIMESTAMP | Event end time                          |
| invited_count   | INT64     | Number of invitees                      |
| cal_platform    | STRING    | `google_calendar` / `outlook` / `other` |

#### `device_telemetry`

| Column              | Type      | Description                     |
| ------------------- | --------- | ------------------------------- |
| telemetry_id        | STRING    | Unique identifier               |
| customer_id         | STRING    | FK to customers                 |
| device_id           | STRING    | Specific device identifier      |
| room_name           | STRING    | Conference room name            |
| timestamp           | TIMESTAMP | When the reading was taken      |
| cpu_usage_pct       | FLOAT64   | CPU usage percentage            |
| memory_usage_pct    | FLOAT64   | Memory usage percentage         |
| network_latency_ms  | FLOAT64   | Network latency in milliseconds |
| packet_loss_pct     | FLOAT64   | Packet loss percentage          |
| video_quality_score | FLOAT64   | Quality score (1.0–5.0)         |

#### `calls`

| Column            | Type      | Description                     |
| ----------------- | --------- | ------------------------------- |
| call_id           | STRING    | Unique identifier               |
| customer_id       | STRING    | FK to customers                 |
| initiator_email   | STRING    | Who started the call            |
| start_timestamp   | TIMESTAMP | Call start time                 |
| duration_minutes  | INT64     | Actual call length              |
| participant_count | INT64     | Number of participants          |
| call_type         | STRING    | `scheduled` / `ad_hoc`          |
| avg_quality_score | FLOAT64   | Average video quality (1.0–5.0) |
| drop_count        | INT64     | Number of drops during call     |

### 3.3 Engagement Problem Signals

The data should be generated such that a subset of customers (~3-4) exhibit clear engagement problems detectable via SQL queries:

| Problem Type              | Signal in Data                                                                           |
| ------------------------- | ---------------------------------------------------------------------------------------- |
| Low login adoption        | Login count / licensed_users ratio significantly below peers in same segment             |
| Meeting underutilization  | Few calendar events relative to licensed users; low invited counts                       |
| Device performance issues | High packet_loss_pct, high network_latency_ms, low video_quality_score in telemetry      |
| Call quality problems     | Low avg_quality_score, high drop_count in calls                                          |
| Declining usage           | Login or call volume trending downward over recent weeks                                 |
| Low ad-hoc adoption       | Very few `ad_hoc` calls — customers only use scheduled meetings, not adopting casual use |

### 3.4 Data Generation Specification

#### Time Range

**7 full weeks (49 days = 35 weekdays + 14 weekend days) ending on the Sunday before the generation date.**

The script computes the end date as the most recent Sunday at or before today, then counts back 49 days (7 weeks) for the start date (a Monday). For example, if run on Wednesday 2026-02-25, the range would be 2026-01-05 (Monday) through 2026-02-22 (Sunday).

Rationale: 7 weeks provides enough history for "trending downward" queries (weeks 1-3 vs weeks 5-7) and always falls before the run date so "past 30 days" queries work naturally. Making the range relative to the generation date keeps the data fresh regardless of when the lab is delivered.

#### Customer Roster (25 total)

**Enterprise (5 customers)**

| Company Name | Licensed Users | Rooms | ACV ($) | Status | CSM |
| --- | --- | --- | --- | --- | --- |
| Pinnacle Financial Group | 1,800 | 120 | 540,000 | PROBLEM: Low login adoption | Sarah Chen |
| Quantum Dynamics Corp | 2,200 | 140 | 660,000 | PROBLEM: Low ad-hoc + call quality | Sarah Chen |
| Atlas Manufacturing | 800 | 65 | 240,000 | Healthy | Michael Torres |
| Meridian Partners | 1,500 | 95 | 450,000 | Healthy | Michael Torres |
| Crestview Holdings | 2,500 | 150 | 750,000 | Healthy | Sarah Chen |

**Mid-Market (10 customers)**

| Company Name | Licensed Users | Rooms | ACV ($) | Status | CSM |
| --- | --- | --- | --- | --- | --- |
| Verdant Health Systems | 320 | 28 | 64,000 | PROBLEM: Meeting underutilization | James Rodriguez |
| Coastal Logistics Inc. | 250 | 35 | 50,000 | PROBLEM: Device performance | Maria Santos |
| Northstar Analytics | 180 | 15 | 36,000 | Healthy | James Rodriguez |
| BlueSky Innovations | 400 | 40 | 80,000 | Healthy | Maria Santos |
| Redwood Consulting | 150 | 12 | 30,000 | Healthy | James Rodriguez |
| Summit Financial | 280 | 22 | 56,000 | Healthy | Maria Santos |
| Ironbridge Solutions | 200 | 18 | 40,000 | Healthy | James Rodriguez |
| Clearwater Tech | 350 | 30 | 70,000 | Healthy | Maria Santos |
| Hawthorne Media | 120 | 10 | 24,000 | Healthy | James Rodriguez |
| Pacific Ridge Partners | 300 | 25 | 60,000 | Healthy | Maria Santos |

**SMB (10 customers)**

| Company Name | Licensed Users | Rooms | ACV ($) | Status | CSM |
| --- | --- | --- | --- | --- | --- |
| BrightPath Education | 55 | 5 | 8,250 | PROBLEM: Declining usage | David Park |
| Ember Creative | 30 | 3 | 4,500 | Healthy | David Park |
| Foxglove Design | 45 | 4 | 6,750 | Healthy | Lisa Wang |
| Garnet Legal | 25 | 2 | 3,750 | Healthy | David Park |
| Horizon Wellness | 70 | 7 | 10,500 | Healthy | Lisa Wang |
| Jade Architects | 20 | 2 | 3,000 | Healthy | David Park |
| Keystone Plumbing | 15 | 2 | 2,250 | Healthy | Lisa Wang |
| Lumen Analytics | 60 | 5 | 9,000 | Healthy | David Park |
| Mosaic Interiors | 35 | 3 | 5,250 | Healthy | Lisa Wang |
| Nimbus Software | 80 | 8 | 12,000 | Healthy | Lisa Wang |

**ACV formula:** Enterprise = $300/user/year, Mid-Market = $200/user/year, SMB = $150/user/year

#### Problem Customer Profiles

**1. Pinnacle Financial Group (Enterprise) — Low Login Adoption**
- Only ~25% of licensed users log in regularly (login rate ~5/user/month vs enterprise baseline of 18)
- Root cause: acquired a competitor 6 months ago; 1,200 of 1,800 seats are from the acquired company and those users still use their legacy tool
- CRM interaction hints: "acquired workforce onboarding stalled", "legacy tool still in use in former Apex offices"
- Detectable via: `COUNT(DISTINCT user_email) / licensed_users` is ~0.25 vs enterprise norm of ~0.75

**2. Quantum Dynamics Corp (Enterprise) — Low Ad-Hoc Adoption + Call Quality Issues**
- Nearly zero ad-hoc calls (97% scheduled vs healthy 65%). Call quality avg 2.8 vs baseline 4.1, drop count avg 2.1 vs baseline 0.2
- Root cause: IT locked down the client (disabled quick-dial features) due to misunderstood security policy; forced proxy routing degrades quality
- CRM interaction hints: "IT security team requires all video traffic through corporate proxy", "users report inability to initiate quick calls"
- Detectable via: `COUNTIF(call_type = 'ad_hoc') / COUNT(*)` is ~3% vs 35% baseline; avg_quality_score ~2.8

**3. Verdant Health Systems (Mid-Market) — Meeting Underutilization**
- Very few calendar events (3/user/month vs mid-market baseline of 10). Login rates are normal — users engage, just not for meetings
- Root cause: organization still uses a separate scheduling tool; Cymbal Meet calendar integration was never properly configured
- CRM interaction hints: "calendar integration support ticket open since November", "users report difficulty connecting Outlook calendars"
- Detectable via: calendar events per licensed user far below segment average, while login rates are normal

**4. Coastal Logistics Inc. (Mid-Market) — Device Performance Issues**
- Telemetry shows: packet loss ~4% (vs 0.3% normal), latency ~95ms (vs 25ms), video quality ~2.2 (vs 4.2). All 35 rooms affected
- Root cause: moved to a new building 2 months ago; network infrastructure has inadequate QoS for video
- CRM interaction hints: "multiple complaints about video freezing since January office relocation", "network team says bandwidth sufficient but QoS not configured"
- Detectable via: all telemetry metrics 3-5x worse than peer devices across ALL rooms

**5. BrightPath Education (SMB) — Declining Usage**
- Usage was healthy in weeks 1-3 but has declined steadily. By weeks 5-7, logins at 40% and calls at 40% of initial levels
- Root cause: key internal champion (VP of Operations) left the company in mid-January; without executive sponsorship, usage is eroding
- CRM interaction hints: "VP of Operations Sarah Kim has departed", "difficulty reaching new point of contact", "renewal at risk"
- Detectable via: week-over-week login and call counts show clear downward slope (>50% decline from weeks 1-3 to weeks 5-7)

#### Segment Baselines (healthy per-user monthly metrics)

| Metric | Enterprise | Mid-Market | SMB |
| --- | --- | --- | --- |
| Logins per user per month | 18 | 15 | 12 |
| Calendar events per user per month | 14 | 10 | 7 |
| Calls per user per month | 12 | 9 | 6 |
| Ad-hoc call ratio | 35% | 30% | 25% |
| Telemetry reports per device | 1 every 5 min (8am–6pm weekdays = 120/day) | 1 every 5 min (8am–6pm weekdays = 120/day) | 1 every 5 min (8am–6pm weekdays = 120/day) |

Each healthy customer's rates should randomly vary +/- 15% from segment baseline so they're not uniform but still cluster around the norm.

#### Normal Telemetry Baselines

| Metric | Healthy Mean | Healthy Std Dev | Units |
| --- | --- | --- | --- |
| cpu_usage_pct | 35.0 | 8.0 | % |
| memory_usage_pct | 45.0 | 10.0 | % |
| network_latency_ms | 25.0 | 8.0 | ms |
| packet_loss_pct | 0.3 | 0.2 | % |
| video_quality_score | 4.2 | 0.3 | 1.0-5.0 scale |

#### Normal Call Quality Baselines

| Metric | Healthy Mean | Healthy Std Dev |
| --- | --- | --- |
| avg_quality_score | 4.1 | 0.4 |
| drop_count | 0.2 | 0.4 (most calls = 0 drops) |

#### Data Volume Targets

| Table | Estimated Rows | Notes |
| --- | --- | --- |
| customers | 25 | Fixed roster above |
| logins | ~315,000 | All licensed users × segment baseline × 1.75 months, reduced by problem customer deficits (Pinnacle ~25% adoption, BrightPath declining) |
| calendar_events | ~53,000 | ~20% of users are meeting organizers; rate is per-organizer |
| device_telemetry | ~3,140,000 | 1 report/device every 5 min, 8am–6pm (120/day), weekdays only. 746 devices × 120 × 35 weekdays |
| calls | ~59,000 | Per-user participation rate ÷ avg participant count (4 enterprise, 3.5 mid-market, 3 SMB) |
| **TOTAL** | **~3,567,000** | Dominated by device telemetry. Well within BigQuery free tier (10 GB storage free) |

#### Distribution Patterns

**Weekday vs Weekend:**

| Activity | Weekdays | Weekends |
| --- | --- | --- |
| Logins | 92% | 8% |
| Calendar events | 95% | 5% |
| Calls | 93% | 7% |
| Device telemetry | 100% | 0% (devices in offices) |

**Day-of-week weights (within weekdays):**

| Day | Weight | Rationale |
| --- | --- | --- |
| Monday | 0.21 | Week kickoff, syncs |
| Tuesday | 0.22 | Peak meeting day |
| Wednesday | 0.21 | High |
| Thursday | 0.20 | Slightly lower |
| Friday | 0.16 | Lighter meeting load |

**Time-of-day weights (for logins, calendar events, and calls — NOT telemetry):**

Device telemetry is a uniform 1-every-5-minutes stream from 8:00–18:00 on weekdays. No time-of-day weighting — every 5-minute mark in the window gets exactly one reading per device.

| Time Block | Weight |
| --- | --- |
| 8:00-9:00 | 0.08 |
| 9:00-10:00 | 0.15 |
| 10:00-12:00 | 0.25 |
| 12:00-13:00 | 0.07 |
| 13:00-15:00 | 0.22 |
| 15:00-17:00 | 0.15 |
| 17:00-19:00 | 0.06 |
| 19:00-8:00 | 0.02 |

**Platform distribution (logins):**

| Platform | Enterprise | Mid-Market | SMB |
| --- | --- | --- | --- |
| desktop | 60% | 55% | 45% |
| web | 25% | 30% | 40% |
| mobile | 15% | 15% | 15% |

**Calendar platform distribution:**

| Platform | Enterprise | Mid-Market | SMB |
| --- | --- | --- | --- |
| google_calendar | 30% | 50% | 70% |
| outlook | 65% | 45% | 25% |
| other | 5% | 5% | 5% |

**Call duration (minutes):**

| Segment | Mean | Std Dev | Min | Max |
| --- | --- | --- | --- | --- |
| Enterprise | 38 | 15 | 5 | 90 |
| Mid-Market | 30 | 12 | 5 | 75 |
| SMB | 25 | 10 | 5 | 60 |

#### CRM Interaction History

Each customer gets 3-8 interactions over the 7-week period:

| Segment | Count | Type Weights |
| --- | --- | --- |
| Enterprise | 6-8 | Health Check 30%, Executive Review 20%, Support 20%, Maintenance 15%, CSM 10%, Renewal Discussion 5% |
| Mid-Market | 4-6 | CSM 30%, Support 25%, Health Check 20%, Maintenance 15%, Renewal Discussion 10% |
| SMB | 3-5 | CSM 35%, Support 30%, Health Check 20%, Maintenance 10%, Renewal Discussion 5% |

Problem customers get interaction notes that hint at their specific issue (as described in profiles above). Healthy customers get generic positive/neutral notes.

#### Reproducibility

- Use `numpy.random.default_rng(seed)` with fixed per-table seeds (not legacy `np.random.seed()`)
- Master seed: `42`. Per-table seeds: customers=1000, logins=2000, calendar_events=3000, device_telemetry=4000, calls=5000
- Each table gets its own seed so modifying one table's generation doesn't shift another
- All timestamps use deterministic integer math relative to the computed start date (only `date.today()` is used — once — to anchor the 7-week window; everything else is deterministic offsets from that anchor)
- User emails: `user_{index}@{company_domain}.com` (deterministic)
- Device IDs: `DEV-{customer_id_prefix}-{room_index:03d}`
- Row IDs: sequential deterministic IDs (e.g., `LOGIN-{counter:07d}`)

**Deployment approach:** `generate_data.py` produces deterministic output. For lab deployment, pre-generate JSONL files and host them in a shared GCS bucket. The student's `setup.sh` copies pre-built files into their BigQuery dataset via `bq load`. This eliminates Python environment variance across students.

#### Design Principle

Problem customers should be **obviously detectable** in simple SQL GROUP BY queries — their metrics should be 2-4 standard deviations from the segment mean. A student running a sorted aggregation should immediately see the outliers without needing sophisticated statistical analysis.

## 4. Reference Content for Interventions

### 4.1 Content Types

Create a small set of fictional Cymbal Meet documents that the Intervention Agent retrieves via Vertex AI Search:

1. **Product Best Practices Guide** — How to drive adoption across an organization (executive sponsorship, department champions, training programs, gamification)
2. **Troubleshooting Guide: Device Performance** — Common device issues and solutions (network configuration, firmware updates, hardware replacement criteria)
3. **Troubleshooting Guide: Call Quality** — Diagnosing and fixing call quality issues (bandwidth requirements, QoS settings, client configuration)
4. **Admin Guide: User Onboarding** — Step-by-step onboarding best practices for new Cymbal Meet users
5. **Intervention Templates** — Template structures for different intervention types (adoption plan, technical remediation plan, executive briefing)

### 4.2 Storage and Retrieval

- Reference documents are authored as markdown in `reference_docs/markdown/`, converted to PDF via `convert_md_to_pdf.sh` (`npx md-to-pdf`), and stored as PDFs in a GCS bucket
- Indexed by a Vertex AI Search datastore (unstructured documents)
- Intervention Agent queries the datastore via `VertexAiSearchTool` to retrieve relevant content based on the customer's specific issues

### 4.3 Vertex AI Search Setup

- **Datastore type:** Unstructured documents
- **Datastore ID:** `cymbal-meet-docs-2` (location: `global`)
- **Data source:** GCS bucket containing reference doc PDFs
- **Integration:** `VertexAiSearchTool` connects directly to the datastore — no separate search app needed
- Setup script (`create_datastore.py`) automates: datastore creation, document import from GCS with FULL reconciliation mode, polling until indexing completes

## 5. Intervention PDF Generation

### 5.1 Approach

- **Templating:** Jinja2 HTML templates with CSS styling
- **Rendering:** WeasyPrint converts styled HTML to PDF
- **Storage:** Write to GCS via the GCS MCP server (custom FastMCP server on Cloud Run). The bucket should be configured with public read access so intervention PDFs are accessible via URL.

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

| Service                  | Purpose                                            |
| ------------------------ | -------------------------------------------------- |
| Agent Engine (Vertex AI) | Agent deployment and management                    |
| BigQuery                 | Customer data storage and querying                 |
| Cloud Storage (GCS)      | Reference docs, intervention PDFs, staging buckets |
| Cloud Run                | Hosts the GCS MCP server                           |
| Cloud Build              | Builds container images for Cloud Run              |
| Artifact Registry        | Stores container images for Cloud Run              |
| Vertex AI Search         | RAG over reference documents                       |
| IAM                      | Service accounts and permissions                   |

### 6.2 APIs to Enable

All APIs must be enabled before any provisioning steps:

```bash
gcloud services enable \
  aiplatform.googleapis.com \
  discoveryengine.googleapis.com \
  bigquery.googleapis.com \
  run.googleapis.com \
  storage.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  cloudresourcemanager.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  compute.googleapis.com \
  iam.googleapis.com
```

Additionally, Vertex AI Search requires activating the AI Applications console at `console.cloud.google.com/gen-app-builder` (Terms of Service acceptance).

### 6.3 Agent Runtime Identity

Agents deployed to Agent Engine run using the **AI Platform Reasoning Engine Service Agent**:

```
service-PROJECT_NUMBER@gcp-sa-aiplatform-re.iam.gserviceaccount.com
```

For the lab, use a **custom service account** passed at deployment time. This is explicit, teachable, and lets students see exactly what permissions are granted:

```python
client.agent_engines.create(
    agent=local_agent,
    config={
        "service_account": "cymbal-agent@PROJECT_ID.iam.gserviceaccount.com",
        "display_name": "Orchestrator Agent",
        "requirements": ["google-cloud-aiplatform[adk,agent_engines]"],
        "staging_bucket": "gs://PROJECT_ID-agent-staging",
    }
)
```

#### Agent Service Account Roles

| Role                           | Purpose                                        |
| ------------------------------ | ---------------------------------------------- |
| `roles/bigquery.dataViewer`    | Read BigQuery tables                           |
| `roles/bigquery.jobUser`       | Execute BigQuery queries                       |
| `roles/storage.objectAdmin`    | Read/write GCS objects (reference docs + PDFs) |
| `roles/aiplatform.user`        | Deploy and manage Agent Engine agents          |
| `roles/discoveryengine.editor` | Query Vertex AI Search datastores              |
| `roles/run.invoker`            | Call the GCS MCP server on Cloud Run           |

#### GCS MCP Server Service Account (Cloud Run)

A separate service account for the Cloud Run-hosted GCS MCP server:

| Role                        | Purpose                              |
| --------------------------- | ------------------------------------ |
| `roles/storage.objectAdmin` | Read/write GCS objects on behalf of agents |

### 6.4 Authentication Flows

| Source → Destination | Mechanism | Notes |
| --- | --- | --- |
| Student locally → GCP APIs | `gcloud auth application-default login` | ADC credentials stored at `~/.config/gcloud/application_default_credentials.json` |
| Orchestrator → Data Agent (A2A) | Vertex AI SDK / ADC | Intra-project Agent Engine calls use the caller's service account automatically |
| Orchestrator → Intervention Agent (A2A) | Vertex AI SDK / ADC | Same as above — no explicit token management needed |
| Data Agent → BigQuery MCP Server | OAuth 2.0 via ADC | Google-hosted MCP at `https://bigquery.googleapis.com/mcp`; agent SA authenticates automatically |
| Intervention Agent → GCS MCP Server (Cloud Run) | OIDC identity token | Agent SA needs `roles/run.invoker` on the Cloud Run service; ADC generates the token |
| Intervention Agent → Vertex AI Search | ADC | Uses `VertexAiSearchTool` from ADK; SA needs `roles/discoveryengine.editor` |
| GCS MCP Server → Cloud Storage | ADC (automatic on Cloud Run) | Cloud Run service account authenticates to GCS automatically |
| Gemini Enterprise → Orchestrator | Google-managed | No student configuration needed |

#### BigQuery MCP Server Configuration

The BigQuery MCP server is Google-hosted (no deployment required). Agent configuration:

```json
{
  "mcpServers": {
    "bigquery": {
      "url": "https://bigquery.googleapis.com/mcp",
      "transport": "http",
      "auth": {
        "type": "oauth2",
        "scope": "https://www.googleapis.com/auth/bigquery"
      }
    }
  }
}
```

#### GCS MCP Server on Cloud Run

The GCS MCP server is a custom Python FastMCP server wrapping `google-cloud-storage`. It exposes three tools (`list_objects`, `read_object`, `write_object`) over Streamable HTTP at `/mcp`. Deploy with authentication required and grant the agent SA invoker access:

```bash
# Deploy with dedicated service account, auth required
bash setup/deploy_gcs_mcp.sh

# Or manually:
gcloud run deploy gcs-mcp-server \
  --source ./setup/gcs-mcp-server/ \
  --service-account=gcs-mcp-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --no-allow-unauthenticated \
  --ingress=all \
  --region=us-central1

# Grant agent SA permission to invoke
gcloud run services add-iam-policy-binding gcs-mcp-server \
  --region=us-central1 \
  --member="serviceAccount:cymbal-agent@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

### 6.5 Publishing to Gemini Enterprise

**Required IAM role:** `roles/discoveryengine.admin`

**Process:**
1. Deploy the orchestrator agent to Agent Engine (produces a reasoning engine resource ID)
2. Register it with a Gemini Enterprise app via the Discovery Engine API or Cloud Console
3. The reasoning engine region must align with the Gemini Enterprise location (e.g., `us-central1` for Gemini `us` location)

**End-user access roles for Gemini Enterprise:**

| Role | Who |
| --- | --- |
| `roles/discoveryengine.admin` | Admins registering/managing agents |
| `roles/discoveryengine.agentspaceUser` | End users interacting with the agent |
| `roles/serviceusage.serviceUsageConsumer` | All Gemini Enterprise users |

### 6.6 Student Environment

- Each student gets their own GCP project (provisioned by Qwiklabs/CloudSkillsBoost)
- Setup script provisions all required resources within the project
- All resource names are parameterized by project ID to avoid collisions

**Local authentication setup:**

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project $PROJECT_ID
```

**Required IAM roles for the deploying student** (typically granted as `roles/owner` in lab environments):

| Role                                 | Purpose                                  |
| ------------------------------------ | ---------------------------------------- |
| `roles/aiplatform.user`             | Deploy and manage Agent Engine agents    |
| `roles/storage.admin`               | Create buckets, manage objects           |
| `roles/bigquery.admin`              | Create datasets, tables, load data       |
| `roles/run.admin`                   | Deploy MCP server to Cloud Run           |
| `roles/iam.serviceAccountAdmin`     | Create and manage service accounts       |
| `roles/iam.serviceAccountUser`      | Deploy with custom service accounts      |
| `roles/discoveryengine.admin`       | Create search datastores/apps, publish agents |
| `roles/serviceusage.serviceUsageAdmin` | Enable APIs                           |

## 7. Infrastructure Setup and Prerequisites

### 7.1 Local Prerequisites

| Tool | Version | Purpose |
| --- | --- | --- |
| Google Cloud CLI (`gcloud`) | Latest (run `gcloud components update`) | Project config, API enablement, IAM, deployments |
| Python | 3.11+ (3.12+ recommended) | Agent development, setup scripts, data generation |
| Node.js / npm | 20+ (optional) | Only needed for MCP Inspector testing (`npx @modelcontextprotocol/inspector`) |
| Docker | Latest (optional) | Local container testing before Cloud Run deployment |

**Python packages:**
```bash
pip install google-cloud-aiplatform[agent_engines,adk] google-adk a2a-sdk \
  google-cloud-bigquery google-cloud-storage jinja2 weasyprint numpy
```

### 7.2 Provisioning Order

Infrastructure must be provisioned in this order due to dependencies. `setup.sh` orchestrates Phases 1–3 in a single run; BigQuery data loading and Cloud Run deployment are separate scripts.

**Phase 1 — Foundation (must be first) — `setup.sh` Phase 1**
1. Enable all APIs (section 6.2), including BigQuery MCP endpoint (`gcloud beta services mcp enable`)
2. Create service accounts: agent SA (`cymbal-agent`) and GCS MCP SA (`gcs-mcp-sa`)
3. Grant IAM roles to both service accounts (section 6.3)
4. Create three GCS buckets: `gs://$PROJECT_ID-agent-staging`, `gs://$PROJECT_ID-cymbal-meet-refs`, `gs://$PROJECT_ID-cymbal-meet-interventions` (public read)
5. Provision Discovery Engine service agent with GCS read access

**Phase 2 — Reference docs + Vertex AI Search — `setup.sh` Phase 2**
6. Create Python venv and install dependencies
7. Convert reference docs from markdown to PDF (`convert_md_to_pdf.sh`)
8. Upload PDFs to the refs GCS bucket (`upload_reference_docs.py`)
9. Create Vertex AI Search datastore and import docs (`create_datastore.py`)
10. **Wait for indexing to complete** — typically 5-10 minutes for small datasets, but can take up to 30 minutes

**Phase 3 — BigQuery data layer (separate scripts)**
11. Create BigQuery dataset `cymbal_meet` and all tables (`create_bq_tables.py`)
12. Generate and load synthetic data into BigQuery (`generate_data.py`)

**Phase 4 — Cloud Run MCP server — `deploy_gcs_mcp.sh`**
13. Deploy GCS MCP server (custom FastMCP) to Cloud Run with `--no-allow-unauthenticated`
14. Grant `roles/run.invoker` to the agent SA on the Cloud Run service
15. Record the Cloud Run service URL for agent MCP configuration

**Phase 5 — Agent deployment**
16. Deploy Data Agent to Agent Engine (references BigQuery MCP)
17. Deploy Intervention Agent to Agent Engine (references Cloud Run MCP URL + Vertex AI Search datastore)
18. Deploy Orchestrator Agent to Agent Engine (references Data Agent and Intervention Agent resource IDs for A2A)
19. Publish Orchestrator to Gemini Enterprise

### 7.3 Vertex AI Search Setup Details

**Create a datastore:**
```bash
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://discoveryengine.googleapis.com/v1/projects/$PROJECT_ID/locations/global/collections/default_collection/dataStores?dataStoreId=cymbal-meet-docs" \
  -d '{
    "displayName": "Cymbal Meet Reference Docs",
    "industryVertical": "GENERIC",
    "solutionTypes": ["SOLUTION_TYPE_SEARCH"],
    "contentConfig": "CONTENT_REQUIRED"
  }'
```

**Import documents from GCS:**
```bash
curl -X POST \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  "https://discoveryengine.googleapis.com/v1/projects/$PROJECT_ID/locations/global/collections/default_collection/dataStores/cymbal-meet-docs/branches/0/documents:import" \
  -d '{
    "gcsSource": {
      "inputUris": ["gs://'$PROJECT_ID'-cymbal-meet-refs/*"],
      "dataSchema": "content"
    },
    "reconciliationMode": "FULL"
  }'
```

**Agent integration** — the Intervention Agent uses ADK's built-in `VertexAiSearchTool`:
```python
from google.adk.tools import VertexAiSearchTool

vertex_search_tool = VertexAiSearchTool(
    data_store_id="projects/PROJECT_ID/locations/global/collections/default_collection/dataStores/cymbal-meet-docs"
)
```

**Constraint:** `VertexAiSearchTool` must be the only tool on its agent instance. If the Intervention Agent also needs other tools (PDF generation, GCS MCP), use a sub-agent within the Intervention Agent dedicated to search, or invoke Vertex AI Search via the Discovery Engine client library as a custom tool instead.

### 7.4 Cloud Run MCP Server Deployment

The GCS MCP server is a custom Python FastMCP server (`setup/gcs-mcp-server/server.py`) wrapping `google-cloud-storage`. It exposes three tools — `list_objects`, `read_object`, `write_object` — over Streamable HTTP at `/mcp`.

**Deployment:**
```bash
# Build and deploy (recommended — handles all steps)
bash setup/deploy_gcs_mcp.sh

# Or manually:
gcloud run deploy gcs-mcp-server \
  --source ./setup/gcs-mcp-server/ \
  --service-account=gcs-mcp-sa@$PROJECT_ID.iam.gserviceaccount.com \
  --no-allow-unauthenticated \
  --ingress=all \
  --region=us-central1

# Grant invoker access to the agent SA
gcloud run services add-iam-policy-binding gcs-mcp-server \
  --region=us-central1 \
  --member="serviceAccount:cymbal-agent@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

**Transport:** Streamable HTTP (preferred). The MCP endpoint is at `/mcp`.

**Agent connection:**
```python
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams
import google.auth.transport.requests
import google.oauth2.id_token

def get_id_token(target_url):
    audience = target_url.split('/mcp')[0]
    request = google.auth.transport.requests.Request()
    return google.oauth2.id_token.fetch_id_token(request, audience)

mcp_url = os.getenv("GCS_MCP_URL")  # e.g., https://gcs-mcp-server-HASH.us-central1.run.app/mcp
mcp_tools = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url=mcp_url,
        headers={"Authorization": f"Bearer {get_id_token(mcp_url)}"},
    ),
)
```

### 7.5 Networking

For the **standard Agent Engine deployment** (used in this lab):
- Agent Engine runs in Google-managed infrastructure with public internet egress
- Cloud Run MCP servers need `--ingress=all` with authentication (`--no-allow-unauthenticated`)
- No VPC configuration required
- No firewall rules needed — IAM authentication on Cloud Run handles access control

### 7.6 Validation Checklist

After setup, verify each component before proceeding to agent deployment:

| Step | Validation Command/Action |
| --- | --- |
| APIs enabled | `gcloud services list --enabled` |
| Service accounts exist | `gcloud iam service-accounts list` |
| BigQuery data loaded | `bq query "SELECT COUNT(*) FROM cymbal_meet.customers"` → 25 |
| Reference docs in GCS | `gsutil ls gs://$PROJECT_ID-cymbal-meet-refs/` |
| Vertex AI Search indexed | Console: AI Applications > Datastore > Activity shows "Import completed" |
| GCS MCP server running | `gcloud run services describe gcs-mcp-server --region=us-central1` |
| Agent staging bucket exists | `gsutil ls gs://$PROJECT_ID-agent-staging/` |

## 8. Technology Stack

| Component            | Technology                                                                                                                                  | Version       |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- | ------------- |
| Agent framework      | Google ADK                                                                                                                                  | Latest stable |
| Inter-agent protocol | A2A (Google)                                                                                                                                | Latest stable |
| BigQuery integration | Google's official BigQuery MCP server                                                                                                       | Latest stable |
| GCS integration      | Custom FastMCP server wrapping `google-cloud-storage` on Cloud Run (`setup/gcs-mcp-server/server.py`)                                          | Latest stable |
| Language             | Python                                                                                                                                      | 3.11+         |
| PDF templating       | Jinja2                                                                                                                                      | Latest stable |
| PDF rendering        | WeasyPrint                                                                                                                                  | Latest stable |
| RAG retrieval        | Vertex AI Search                                                                                                                            | Latest        |
| Agent deployment     | Agent Engine (Vertex AI)                                                                                                                    | Latest        |
| MCP server hosting   | Cloud Run                                                                                                                                   | Latest        |
| End-user interface   | Gemini Enterprise                                                                                                                           | Latest        |

## 9. Directory Structure

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
│   ├── deploy_gcs_mcp.sh           # Deploys custom GCS MCP server to Cloud Run
│   └── create_datastore.py          # Creates Vertex AI Search datastore
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
│       ├── mcp_config.json         # GCS MCP server configuration (Cloud Run URL)
│       ├── pdf_generator.py        # WeasyPrint + Jinja2 PDF generation
│       └── templates/
│           └── intervention.html   # HTML/CSS template for intervention PDFs
├── deploy/
│   ├── deploy_agents.py            # Deploys all agents to Agent Engine
│   └── publish_to_gemini.py        # Publishes orchestrator to Gemini Enterprise
├── requirements.txt                # Python dependencies
└── README.md                       # Setup and usage instructions
```

## 10. Example End-to-End Flow

**User prompt in Gemini Enterprise:**
> "Create interventions for customers that have an engagement shortfall in scheduled meeting events"

**Step 1 — Orchestrator delegates data question:**
- Orchestrator interprets the user's request and formulates a natural language data question
- Sends to Data Agent via A2A: "Which customers have significantly fewer calendar events per licensed user than their segment average over the past 30 days?"

**Step 2 — Data Agent translates and executes:**
- Data Agent interprets the natural language question
- Composes a SQL query joining `customers` and `calendar_events`, computing per-customer event rates vs. segment averages
- Executes query against BigQuery via MCP
- Returns structured results: list of customers with low meeting engagement, their metrics, and context

**Step 3 — Orchestrator processes results:**
- Identifies Verdant Health Systems as the customer with meeting underutilization
- Prepares a context payload (customer info, specific metrics, issue type)
- Sends to Intervention Agent via A2A

**Step 4 — Intervention Agent creates documents:**
- For each customer:
  - Queries Vertex AI Search for relevant best practices and troubleshooting content
  - Generates a tailored intervention document
  - Renders to PDF via WeasyPrint
  - Writes PDF to GCS via the GCS MCP server (Cloud Run) at `gs://{bucket}/{customer_id}/...`
  - Returns the public URL

**Step 5 — Orchestrator presents results:**
- Collects all intervention links
- Presents to the user:
  ```
  Intervention created for 1 customer with meeting engagement shortfall:

  1. Verdant Health Systems (Mid-Market) — Only 3 calendar events per user/month
     vs segment average of 10. Login rates are normal, suggesting a calendar
     integration issue rather than overall disengagement.
     CSM: James Rodriguez
     Intervention: https://storage.googleapis.com/.../verdant_health/2026-02-25_adoption_abc123.pdf

  Recommended next step: Review the intervention and share with James Rodriguez
  for customer outreach. The intervention recommends prioritizing calendar
  integration configuration with the customer's IT team.
  ```
