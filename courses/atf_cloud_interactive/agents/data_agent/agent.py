"""Data agent variant using ADK's built-in auth_scheme + auth_credential.

Instead of baking a static OAuth token into the connection headers at module
load time, this variant uses ADK's credential management pipeline:

  - auth_scheme:  OAuth2 clientCredentials flow pointing at Google's token URL
  - auth_credential:  SERVICE_ACCOUNT with use_default_credential=True (ADC)

On each tool invocation the ADK CredentialManager exchanges the service-account
credential for a fresh Bearer token via ServiceAccountCredentialExchanger.
This follows the official mcp_service_account_agent sample:
https://github.com/google/adk-python/blob/main/contributing/samples/mcp_service_account_agent/agent.py
"""

import logging
import os
import warnings
from functools import cached_property

from dotenv import load_dotenv

load_dotenv()

import google.auth
from fastapi.openapi.models import (OAuth2, OAuthFlowClientCredentials,
                                    OAuthFlows)
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents.llm_agent import LlmAgent
from google.adk.auth.auth_credential import (AuthCredential,
                                             AuthCredentialTypes,
                                             ServiceAccount)
from google.adk.models import Gemini
from google.adk.runners import InMemoryRunner
from google.adk.telemetry.google_cloud import (get_gcp_exporters,
                                               get_gcp_resource)
from google.adk.telemetry.setup import maybe_set_otel_providers
from google.adk.tools.mcp_tool.mcp_session_manager import \
    StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.genai import Client, types

# TODO MODELARMOR IMPORT: Import ModelArmorSafetyFilterPlugin from model_armor_plugin.

# --- Environment configuration ---
PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]

# Suppress repetitive ADK experimental-feature warnings and noisy INFO logs
warnings.filterwarnings("ignore", message=r"\[EXPERIMENTAL\]")
logging.getLogger("google.adk").setLevel(logging.WARNING)
logging.getLogger("google.genai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


# TODO TELEMETRY: Export OpenTelemetry Logging and Traces to Google Cloud.
# Steps:
#   1. Obtain default GCP credentials (scoped to cloud-platform).
#   2. Create GCP exporters with Cloud Tracing and Cloud Logging enabled.
#   3. Wire everything together with maybe_set_otel_providers().


# TODO MCP SCOPES: Define the BigQuery MCP toolset configuration.
# Steps:
#   1. Set BIGQUERY_MCP_ENDPOINT to the BigQuery MCP URL.
#   2. Define BIGQUERY_SCOPES with cloud-platform and bigquery scopes.

def _create_bigquery_mcp_toolset() -> McpToolset:
    # TODO MCP TOOLSET: Create and return an McpToolset for BigQuery.
    # Steps:
    #   1. Set connection_params using StreamableHTTPConnectionParams with the MCP endpoint URL.
    #   2. Set auth_scheme to OAuth2 with a clientCredentials flow pointing at Google's token URL.
    #   3. Set auth_credential to a SERVICE_ACCOUNT type using ADC (use_default_credential=True).
    pass


# --- System prompt ---
DATA_AGENT_INSTRUCTION = f"""\
You are the Cymbal Meet data domain expert. You accept natural language questions
and translate them into SQL queries against BigQuery.

## Target Dataset
The user may specify a project and dataset to query. If they do, use those values
for all MCP tool calls and SQL queries. If they don't, use these defaults:
- **projectId**: `{PROJECT_ID}`
- **datasetId**: `cymbal_meet`

Throughout the instructions below, `<PROJECT>` and `<DATASET>` refer to whichever
values are in effect (user-provided or default).

## Know the Schema Before You Query
NEVER reference a column name you have not confirmed via `get_table_info` earlier
in this conversation. If you are unsure of any column name, call `get_table_info`
FIRST — guessing column names causes query failures.

Use the MCP tools to learn table structures — do NOT hardcode them:
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

## Identifying Underperforming Customers
When asked to find customers with engagement issues or underperformance:
1. First compute the **segment average** for each relevant metric.
2. Flag any customer whose metric is **below 75% of their segment average**
   (i.e., more than 25% worse than the segment average).
3. Always return both the customer's value AND the segment average so the caller
   can see the gap.
4. For device metrics where higher is worse (packet_loss, latency), flag customers
   whose value is **above 133% of the segment average** (i.e., more than 33% worse).

Do NOT use arbitrary absolute thresholds unless the caller explicitly provides them.
The comparison should always be relative to the segment.

## Output Format
Return structured results with clear headers. Format numbers readably (e.g.,
percentages as "25.3%", currency as "$540,000"). ALWAYS include segment averages
alongside individual customer metrics so the caller can see how each customer
compares to their peers.

## Constraints
- **Read-only**: Only SELECT queries via `execute_sql`. Never INSERT, UPDATE, DELETE, or DDL.
- **Conversational memory**: If you already discovered a table's schema earlier
  in this conversation, reuse that knowledge instead of calling `get_table_info` again.
- **Efficiency**: Avoid SELECT * on large tables. Use specific columns and
  appropriate WHERE/LIMIT clauses.

## Error Recovery
If `execute_sql` returns an error (e.g. "Unrecognized name"), you may retry
**once**: call `get_table_info` to re-confirm the schema, fix the query, and
re-execute. If the retry also fails, report the error to the user and stop.


## Progress Updates
Before each major step, output a brief status line so the calling agent
can relay progress to the user:
- Before composing a query: "Composing query for [topic]..."
- Before executing SQL: "Executing query for [topic]..."
- Before interpreting results: "Interpreting results for [topic]..."
- Etc.
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
                retry_options=types.HttpRetryOptions(
                    max_delay=7,
                    exp_base=1.5,
                    jitter=.5,
                )
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
    tools=[
        # TODO MCP TOOL: Call _create_bigquery_mcp_toolset() here.
    ],
)

# TODO MODELARMOR RUNNER: Create an InMemoryRunner with the ModelArmorSafetyFilterPlugin.
# Steps:
#   1. Create an InMemoryRunner with agent=root_agent and app_name="data_agent".
#   2. Pass plugins=[ModelArmorSafetyFilterPlugin()] to enable Model Armor safety filtering.

# TODO A2A APP: Create the A2A application using to_a2a().
# Steps:
#   1. Call to_a2a() with root_agent, agent_card="agent_card.json", and runner=runner.