# JWD1: Setup Streamlining & Data Agent Deployment Testing Plan

---

## Part 1: Setup Process Streamlining

### Current Flow

The setup is spread across 3 phases with multiple manual steps:

1. **Phase 1** — `setup.sh` (infra + reference docs + Vertex AI Search)
2. **Phase 2** — Manual: `create_bq_tables.py` → `generate_data.py`
3. **Phase 3** — Manual: `deploy_gcs_mcp.sh`

### Recommendations

#### 1. Fold BigQuery steps into `setup.sh`

`create_bq_tables.py` and `generate_data.py` are not called by `setup.sh`, even though the venv and dependencies are already set up there. Adding them as Phase 2 steps inside `setup.sh` would eliminate the need for the user to manually activate the venv and run two separate commands. The scripts are already idempotent (`exists_ok=True`, `WRITE_TRUNCATE`), so re-running is safe.

**Suggested addition to `setup.sh`:**
```bash
# ── Phase 2: BigQuery data layer ──
echo "Creating BigQuery tables..."
python create_bq_tables.py

echo "Generating and loading synthetic data..."
python generate_data.py
```

#### 2. Combine `create_bq_tables.py` into `generate_data.py`

`create_bq_tables.py` creates the dataset and 5 empty tables. `generate_data.py` then populates them. Since `generate_data.py` uses `WRITE_TRUNCATE` (which auto-creates tables if they don't exist with the right job config), or at minimum already has full knowledge of the schema, these could be a single script. The table-creation step is small (~100 lines) and could live as a `create_tables()` function at the top of `generate_data.py`.

This reduces the number of scripts a student (or instructor) needs to understand and removes a potential ordering mistake.

**Tradeoff:** Keeping them separate is fine if you want students to explicitly learn schema-first design. If this is a teaching moment, leave them separate but call both from `setup.sh`.

#### 3. Remove the Node.js dependency for PDF conversion

`convert_md_to_pdf.sh` requires `npx md-to-pdf`, which pulls in Node.js as a dependency on top of the Python ecosystem already in use. Alternatives:

- **Pre-commit the PDFs to the repo.** The markdown sources are version-controlled, the PDFs are derived artifacts. Since these are 5 static docs that rarely change, just commit the PDFs and skip the conversion step entirely during setup. The conversion script stays as a dev tool for when docs are updated.
- **Use a Python-based converter** (e.g., `markdown` + `weasyprint`, which you're already planning to use for the Intervention Agent). This keeps the toolchain to Python only.

The simplest path: commit the PDFs and remove `convert_md_to_pdf.sh` from the setup flow. It can remain as a utility script for doc authors.

#### 4. Add a single `setup_all.sh` or unify into one command

Right now an instructor must:
1. Run `setup.sh`
2. Wait for Vertex AI Search indexing
3. Manually run `create_bq_tables.py`
4. Manually run `generate_data.py`
5. Run `deploy_gcs_mcp.sh`

Proposal: Make `setup.sh` the single entry point that runs everything in order, with clear phase banners and a summary at the end. The GCS MCP deployment (`deploy_gcs_mcp.sh`) could also be folded in as the final phase, since it depends only on SAs and APIs that are already provisioned.

```bash
./setup.sh          # Does everything: APIs, SAs, buckets, PDFs, Vertex AI Search,
                    # BigQuery tables, synthetic data, GCS MCP deploy
```

#### 5. Clean up stale/accidental files from the repo

The git status shows some artifacts that should be cleaned up:

- `setup/--project=jwd-atf-int` — Looks like a mistyped gcloud command created a file named after a flag
- `setup/service-906184221373@gcp-sa-discoveryengine.iam.gserviceaccount.com` — A service account email accidentally created as a file

These should be deleted and added to `.gitignore` if there's a pattern to prevent recurrence.

#### 6. Add a validation/smoke-test step at the end of setup

After all resources are provisioned, add a validation block that confirms:
- BigQuery dataset exists and all 5 tables have expected row counts
- GCS buckets exist and contain expected objects
- Vertex AI Search datastore is accessible (and optionally, indexing is complete)
- GCS MCP server responds to a health check
- Service accounts exist with correct roles

`setup.sh` already has some of this (it checks bucket/SA existence), but a consolidated "Setup Validation" section at the end would give confidence that everything worked.

#### 7. Parameterize the Vertex AI Search datastore ID

The datastore is currently hardcoded as `cymbal-meet-docs-2` (the `-2` suggests an earlier `cymbal-meet-docs` existed). This should be a variable at the top of the script, consistent with how `PROJECT_ID` and `REGION` are handled.

#### 8. Consider a Makefile or task runner

For a project with this many scripts, a `Makefile` (or `just` / `task`) provides discoverability:

```makefile
setup-infra:    ## Phase 1: APIs, SAs, buckets
setup-data:     ## Phase 2: BigQuery tables + synthetic data
setup-search:   ## Phase 3: Reference docs + Vertex AI Search
setup-mcp:      ## Phase 4: GCS MCP server deployment
setup-all:      ## Run everything in order
validate:       ## Verify all resources are correctly provisioned
clean:          ## Tear down all resources
```

This is optional but useful for a teaching context where students benefit from seeing named targets.

---

### Summary of Streamlining Impact

| Change                                    | Effort     | Impact                              |
| ----------------------------------------- | ---------- | ----------------------------------- |
| Fold BQ steps into setup.sh               | Low        | Eliminates 2 manual steps           |
| Merge create_bq_tables into generate_data | Low        | One less script to track            |
| Pre-commit PDFs, skip Node.js dep         | Low        | Removes entire toolchain dependency |
| Unify all phases into single setup.sh     | Medium     | One-command setup                   |
| Clean stale files                         | Trivial    | Repo hygiene                        |
| Add validation step                       | Medium     | Confidence in setup correctness     |
| Parameterize datastore ID                 | Trivial    | Consistency                         |
| Makefile                                  | Low-Medium | Discoverability (optional)          |

---

## Part 2: Data Agent Deployment Testing Plan

### Goal

Deploy the Data Agent to **Agent Engine** (Vertex AI) and verify it works correctly in the cloud environment — specifically that it can connect to BigQuery via MCP, discover schema at runtime, and answer questions about the synthetic data.

### Pre-Deployment Checklist

Before deploying, confirm:

- [ ] `setup.sh` has completed (APIs enabled, SAs created, staging bucket exists)
- [ ] BigQuery tables are populated (`generate_data.py` has run)
- [ ] `adk web` local testing passes (agent answers questions correctly locally)
- [ ] `GOOGLE_CLOUD_PROJECT` is set correctly
- [ ] The `cymbal-agent@` SA has the required roles (bigquery.dataViewer, bigquery.jobUser, aiplatform.user)
- [ ] BigQuery MCP endpoint is enabled (`gcloud beta services mcp enable bigquery.googleapis.com`)

### Step 1: Create the Deployment Script

Create `deploy_data_agent.py` in `setup/` (or `agents/`):

```python
import vertexai
from vertexai import agent_engines

vertexai.init(
    project="PROJECT_ID",
    location="us-central1",
    staging_bucket="gs://PROJECT_ID-agent-staging",
)

agent_engine = agent_engines.create(
    agent_engine=AdkApp(
        agent=root_agent,
        enable_session=True,
    ),
    requirements=[
        "google-adk",
        "google-auth",
        "google-cloud-bigquery",
        "google-genai",
    ],
    display_name="cymbal-meet-data-agent",
    description="Cymbal Meet data domain expert — translates natural language to BigQuery SQL",
)

print(f"Resource name: {agent_engine.resource_name}")
```

**Critical consideration: the Gemini3 location workaround.**

The `Gemini3` subclass in `agent.py` forces `location='global'` for the Gemini API client, which conflicts with Agent Engine's regional location (`us-central1`). The current code uses a `@cached_property` override on `api_client`. During `AdkApp.set_up()`, the agent is instantiated in the Agent Engine environment, so the workaround must travel with the deployment. Verify that:

1. The `Gemini3` subclass is included in the deployed code
2. The `location='global'` override actually takes effect inside Agent Engine (not overridden by the runtime)
3. The ADC token in Agent Engine has the `cloud-platform` scope (it should by default for the agent SA)

### Step 2: Deploy and Capture Resource Name

```bash
cd agents/data_agent
python ../../setup/deploy_data_agent.py
# Output: projects/PROJECT_ID/locations/us-central1/reasoningEngines/RESOURCE_ID
```

Save the resource name — you'll need it for testing and for the Orchestrator's A2A connection later.

### Step 3: Verification Test Suite

Run these tests against the deployed agent, in order. Each test validates a specific capability.

#### Test 3.1: Basic Connectivity

**Query:** "What tables are available in the cymbal_meet dataset?"

**Expected behavior:**
- Agent calls `list_table_ids` via BigQuery MCP
- Returns all 5 tables: customers, logins, calendar_events, device_telemetry, calls

**What this validates:** BigQuery MCP connectivity from Agent Engine, MCP tool invocation works, authentication (Bearer token from SA) is valid.

**Failure modes:**
- 403 on `tools/call` → BigQuery MCP endpoint not enabled (`gcloud beta services mcp enable`)
- Connection timeout → Network/firewall issue in Agent Engine environment
- Empty response → Wrong project ID or dataset name

#### Test 3.2: Schema Discovery

**Query:** "Describe the schema of the customers table, including any nested fields."

**Expected behavior:**
- Agent calls `get_table_info` for the customers table
- Returns all columns with types, including the `interactions` REPEATED RECORD with its subfields (interaction_date, type, contact_name, note)

**What this validates:** Schema introspection works, agent correctly identifies nested/repeated fields.

#### Test 3.3: Simple Aggregation

**Query:** "How many customers are in each segment?"

**Expected behavior:**
- Agent writes and executes: `SELECT segment, COUNT(*) FROM cymbal_meet.customers GROUP BY segment`
- Returns 3 segments with counts (expected: mix of Enterprise, Mid-Market, SMB totaling 25)

**What this validates:** SQL generation, query execution, result formatting.

#### Test 3.4: Cross-Table Join

**Query:** "What is the average number of logins per licensed user for each customer in the last 30 days? Show the top 5 and bottom 5."

**Expected behavior:**
- Agent joins `customers` and `logins` tables
- Calculates per-user login rates
- Pinnacle should appear in the bottom 5 (~25% adoption → low logins/user)

**What this validates:** Multi-table joins, date filtering, ordering, the agent's ability to normalize metrics (logins per *licensed user*, not just total logins).

#### Test 3.5: Nested Record Handling (UNNEST)

**Query:** "Show me all CRM interactions for Pinnacle in the last 60 days."

**Expected behavior:**
- Agent uses `UNNEST(interactions)` syntax correctly
- Returns interaction records with dates, types, contact names, and notes
- Notes should reference adoption/migration issues

**What this validates:** The system prompt's UNNEST() teaching is working, nested record queries don't fail.

**Failure mode:** `Cannot access field interactions on a value with type ARRAY<STRUCT<...>>` → Agent forgot to UNNEST.

#### Test 3.6: Problem Customer Detection

**Query:** "Which customers have average call quality scores below 3.5? Include their segment and the number of calls."

**Expected behavior:**
- Agent queries `calls` table with aggregation
- Quantum should appear prominently (~2.8 avg quality vs 4.1 baseline)
- Possibly Coastal (device performance issues may affect call quality)

**What this validates:** The synthetic data's problem profiles are detectable via natural language queries.

#### Test 3.7: Trend Analysis

**Query:** "Show me week-over-week login trends for BrightPath over the last 7 weeks."

**Expected behavior:**
- Agent calculates weekly login counts for BrightPath
- Should show declining pattern matching the decay curve: [1.0, 1.0, 1.0, 0.85, 0.65, 0.45, 0.35]
- Agent formats results clearly with week labels

**What this validates:** Time-series analysis, the agent can detect engagement decay patterns.

#### Test 3.8: Conversational Context / Memory

**Queries (sequential in same session):**
1. "How many customers are in the Enterprise segment?"
2. "What's the average contract value for those customers?"
3. "Show me the login activity for the one with the lowest contract value."

**Expected behavior:**
- Agent retains context across turns
- Second query references "those customers" (Enterprise segment) without re-asking
- Third query identifies a specific customer and pivots to login data

**What this validates:** Session state works in Agent Engine, agent maintains conversational context.

#### Test 3.9: Edge Cases

**Query:** "Show me all data for customer_id 'NONEXISTENT'."

**Expected behavior:**
- Agent executes query, returns empty result set
- Communicates clearly: "No data found for that customer ID"
- Does NOT hallucinate data

**What this validates:** Graceful handling of empty results.

#### Test 3.10: Read-Only Enforcement

**Query:** "Delete all records from the logins table."

**Expected behavior:**
- Agent refuses — system prompt restricts to SELECT-only
- Responds with something like: "I can only run read-only queries. I'm not able to modify data."

**What this validates:** Safety constraint works in production.

### Step 4: Automated Test Script

Create `test_deployed_agent.py` for repeatable verification:

```python
"""
Smoke tests for deployed Data Agent on Agent Engine.

Usage:
    python test_deployed_agent.py --resource-name=projects/PROJECT/locations/REGION/reasoningEngines/ID
"""

import argparse
import vertexai
from vertexai import agent_engines

def test_agent(resource_name: str):
    vertexai.init(project=PROJECT_ID, location="us-central1")
    agent = agent_engines.get(resource_name)

    session = agent.create_session(user_id="test-user")

    tests = [
        {
            "name": "table_listing",
            "query": "What tables are in the cymbal_meet dataset?",
            "expect_contains": ["customers", "logins", "calls"],
        },
        {
            "name": "segment_count",
            "query": "How many customers per segment?",
            "expect_contains": ["Enterprise", "Mid-Market", "SMB"],
        },
        {
            "name": "nested_record",
            "query": "Show CRM interactions for Pinnacle.",
            "expect_contains": ["Pinnacle", "interaction"],
        },
        {
            "name": "problem_detection",
            "query": "Which customers have avg call quality below 3.5?",
            "expect_contains": ["Quantum"],
        },
        {
            "name": "read_only",
            "query": "Delete all records from the logins table.",
            "expect_contains": ["cannot", "read-only", "SELECT"],
            "expect_any": True,  # any one of these keywords
        },
    ]

    for test in tests:
        print(f"\n--- {test['name']} ---")
        response = agent.stream_query(
            user_id="test-user",
            session_id=session["id"],
            message=test["query"],
        )
        full_response = ""
        for chunk in response:
            if hasattr(chunk, "text"):
                full_response += chunk.text

        print(f"Q: {test['query']}")
        print(f"A: {full_response[:300]}...")

        keywords = test["expect_contains"]
        if test.get("expect_any"):
            passed = any(kw.lower() in full_response.lower() for kw in keywords)
        else:
            passed = all(kw.lower() in full_response.lower() for kw in keywords)

        print(f"PASS" if passed else f"FAIL (expected: {keywords})")
```

### Step 5: Performance & Cost Check

After the functional tests pass, verify:

- **Latency:** First query (cold start + schema discovery) should complete in <30s. Subsequent queries (schema cached in context) should be <15s.
- **Token usage:** Monitor Vertex AI usage dashboard. Schema discovery adds ~500-1000 tokens per new table inspected. Conversational context grows linearly with session length.
- **Cost:** Agent Engine charges per prediction request + Gemini token usage. For a 25-customer dataset, a typical testing session (10-15 queries) should cost <$1.

### Step 6: Teardown (Optional)

If testing reveals issues and you need to redeploy:

```python
# Delete the deployed agent
agent_engines.delete(resource_name, force=True)

# Redeploy after fixes
# ... (repeat Step 2)
```

### Known Risks & Mitigations

| Risk                                                              | Mitigation                                                                                                        |
| ----------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Gemini3 `location='global'` override doesn't work in Agent Engine | Test early. If broken, may need to pass model config differently or use env var manipulation in `AdkApp.set_up()` |
| BigQuery MCP Bearer token expires                                 | Agent Engine should use SA credentials with auto-refresh. Verify token refresh works for long sessions            |
| Cold start latency on Agent Engine                                | First query may take 30-60s. Pre-warm with a lightweight query before demo                                        |
| Schema discovery fails on first query                             | Ensure `list_table_ids` and `get_table_info` tools are available in the MCP toolset. Check MCP tool registration  |
| Session state lost between queries                                | Confirm `enable_session=True` in AdkApp config. Test multi-turn conversations explicitly (Test 3.8)               |
| Agent hallucinates SQL syntax                                     | The system prompt teaches UNNEST explicitly. If hallucination persists, add few-shot examples to the prompt       |