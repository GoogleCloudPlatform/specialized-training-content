import os
from functools import cached_property

import google.auth
import google.auth.transport.requests
from google.adk.agents.llm_agent import LlmAgent
from google.adk.models import Gemini
from google.adk.tools.mcp_tool.mcp_session_manager import \
    StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.genai import Client, types
from vertexai import agent_engines

# --- Environment configuration ---
# All env vars are set in .env (loaded automatically by ADK).
PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]

# --- BigQuery MCP toolset ---
# Authenticate via ADC and pass Bearer token to the Google-hosted BQ MCP endpoint.
# Token is obtained at module load time. For long-running dev sessions, restart
# the ADK dev server to refresh.
BIGQUERY_MCP_ENDPOINT = "https://bigquery.googleapis.com/mcp"
BIGQUERY_SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/bigquery",
]


def _create_bigquery_mcp_toolset() -> McpToolset:
    credentials, _ = google.auth.default(scopes=BIGQUERY_SCOPES)
    credentials.refresh(google.auth.transport.requests.Request())
    return McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url=BIGQUERY_MCP_ENDPOINT,
            headers={"Authorization": f"Bearer {credentials.token}"},
        )
    )

# --- System prompt ---
DATA_AGENT_INSTRUCTION = f"""\
You are the Cymbal Meet data domain expert. You accept natural language questions
about customer engagement and translate them into SQL queries against BigQuery.

## Target Dataset
The user may specify a project and dataset to query. If they do, use those values
for all MCP tool calls and SQL queries. If they don't, use these defaults:
- **projectId**: `{PROJECT_ID}`
- **datasetId**: `cymbal_meet`

Throughout the instructions below, `<PROJECT>` and `<DATASET>` refer to whichever
values are in effect (user-provided or default).

## Schema Discovery
Use the MCP tools to discover schema — do NOT hardcode table structures:
1. **List tables**: call `list_table_ids` with projectId=`<PROJECT>` and datasetId=`<DATASET>`
2. **Inspect a table**: call `get_table_info` with projectId=`<PROJECT>`, datasetId=`<DATASET>`, and the tableId
3. **Sample data** (if needed): use `execute_sql` with `SELECT * FROM <PROJECT>.<DATASET>.<TABLE> LIMIT 5`

## Nested Field Handling
When `get_table_info` shows a field with type RECORD and mode REPEATED, you MUST
use UNNEST() to query it. Example:
```sql
SELECT c.customer_id, i.type, i.notes
FROM `<PROJECT>.<DATASET>.customers` c,
UNNEST(c.interactions) AS i
```

## Output Format
Return structured results with clear headers. Format numbers readably (e.g.,
percentages as "25.3%", currency as "$540,000"). When comparing customers,
include relevant benchmarks or segment averages for context.

## Constraints
- **Read-only**: Only SELECT queries via `execute_sql`. Never INSERT, UPDATE, DELETE, or DDL.
- **Conversational memory**: If you already discovered a table's schema earlier
  in this conversation, reuse that knowledge instead of calling `get_table_info` again.
- **Efficiency**: Avoid SELECT * on large tables. Use specific columns and
  appropriate WHERE/LIMIT clauses.
"""

class Gemini3(Gemini):
    """Gemini subclass that forces location='global' for Gemini 3 models."""

    @cached_property
    def api_client(self) -> Client:
        return Client(
            project=os.environ["GOOGLE_CLOUD_PROJECT"],
            location="global",
            http_options=types.HttpOptions(
                headers=self._tracking_headers(),
                retry_options=self.retry_options,
                # base_url=self.base_url,
            ),
        )

# --- Agent definition ---
root_agent = LlmAgent(
    model=Gemini3(model="gemini-3-flash-preview"),
    name="data_agent",
    description=(
        "Cymbal Meet data domain expert. Accepts natural language questions "
        "about customer engagement, translates to SQL, executes via BigQuery, "
        "returns structured results."
    ),
    instruction=DATA_AGENT_INSTRUCTION,
    tools=[_create_bigquery_mcp_toolset()],
)

app = agent_engines.AdkApp(agent=root_agent)