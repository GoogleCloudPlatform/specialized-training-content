"""Improve Engagement agent — A2A client coordinating Data + Intervention agents.

Deploys to Agent Engine via `adk deploy agent_engine`. The Improve Engagement agent is
NOT an A2A server — it is the user-facing agent that delegates data questions
to the Data Agent and intervention creation to the Intervention Agent, both via
their Cloud Run A2A endpoints.
"""

import logging
import os
import warnings
from functools import cached_property

from dotenv import load_dotenv

load_dotenv()

import google.auth
import google.auth.transport.requests
import google.oauth2.id_token
import httpx
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.models import Gemini
from google.adk.telemetry.google_cloud import (get_gcp_exporters,
                                               get_gcp_resource)
from google.adk.telemetry.setup import maybe_set_otel_providers
from google.genai import Client, types

# --- Environment configuration ---
PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
DATA_AGENT_URL = os.environ["DATA_AGENT_URL"]  # Cloud Run base URL
INTERVENTION_AGENT_URL = os.environ["INTERVENTION_AGENT_URL"]  # Cloud Run base URL

# Suppress repetitive ADK experimental-feature warnings and noisy INFO logs
warnings.filterwarnings("ignore", message=r"\[EXPERIMENTAL\]")
logging.getLogger("google.adk").setLevel(logging.WARNING)
logging.getLogger("google.genai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# # --- Telemetry ---
# _gcp_creds, _gcp_project = google.auth.default(
#     scopes=["https://www.googleapis.com/auth/cloud-platform"],
# )
# _gcp_exporters = get_gcp_exporters(
#     enable_cloud_tracing=True,
#     enable_cloud_logging=True,
#     google_auth=(_gcp_creds, _gcp_project),
# )
# _gcp_resource = get_gcp_resource(project_id=PROJECT_ID)
# maybe_set_otel_providers(
#     otel_hooks_to_setup=[_gcp_exporters],
#     otel_resource=_gcp_resource,
# )


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
            ),
        )

class _CloudRunAuth(httpx.Auth):
    """httpx Auth that attaches OIDC identity tokens for Cloud Run."""

    def __init__(self, audience: str):
        self._audience = audience

    def auth_flow(self, request):
        if request.url.host in ("localhost", "127.0.0.1"):
            yield request
            return
    
        auth_request = google.auth.transport.requests.Request()
        token = google.oauth2.id_token.fetch_id_token(
            auth_request, audience=self._audience
        )
        request.headers["Authorization"] = f"Bearer {token}"
        yield request


# --- Remote Data Agent (A2A client) ---
_data_agent_http = httpx.AsyncClient(
    auth=_CloudRunAuth(DATA_AGENT_URL),
    timeout=httpx.Timeout(timeout=600.0),
)

data_agent = RemoteA2aAgent(
    name="data_agent",
    description=(
        "Cymbal Meet data domain expert. Accepts natural language questions "
        "and translates them to SQL, executes via BigQuery, "
        "and returns structured results. Delegate ALL data-related questions "
        "to this agent — never attempt to query data directly."
    ),
    agent_card=f"{DATA_AGENT_URL}/.well-known/agent.json",
    httpx_client=_data_agent_http,
)


# --- Remote Intervention Agent (A2A client) ---
_intervention_agent_http = httpx.AsyncClient(
    auth=_CloudRunAuth(INTERVENTION_AGENT_URL),
    timeout=httpx.Timeout(timeout=600.0),
)

intervention_agent = RemoteA2aAgent(
    name="intervention_agent",
    description=(
        "Cymbal Meet intervention specialist. Accepts customer engagement data "
        "(customer_id, customer_name, problem_profile, engagement_metrics), "
        "searches for relevant best-practice content via Vertex AI Search, "
        "and generates a personalized intervention PDF uploaded to GCS. "
        "Delegate ALL intervention creation to this agent."
    ),
    agent_card=f"{INTERVENTION_AGENT_URL}/.well-known/agent.json",
    httpx_client=_intervention_agent_http,
)


# --- Improve Engagement agent system prompt ---
IMPROVE_ENGAGEMENT_INSTRUCTION = """\
You are the Cymbal Meet Improve Engagement Agent. You help customer success teams
identify product engagement issues and create intervention documents to address them.

You are a coordinator. You have two sub-agents and NO direct capabilities:
- **data_agent**: Runs BigQuery queries. Delegate ALL data questions here.
- **intervention_agent**: Generates branded PDF intervention documents and uploads
  them to Cloud Storage. Delegate ALL intervention creation here.

You MUST use these agents — you cannot query data or create interventions yourself.

## Workflow

Follow these phases in order. Complete each phase before starting the next.

### Phase 1 — Interpret the request
Determine what data is needed based on the user's question:
- If the user asks about a particular customer, focus on that customer's data and
  compare against their segment and overall averages.
- If the user asks about a segment, look for engagement issues across all customers
  in that segment.
- If the user asks about a category of issues (e.g. video quality), focus on that
  category across relevant customers.
- Otherwise, scan for all types of engagement issues across all customers.

Typical engagement issues include:
- Low login adoption (low % of licensed users logging in monthly)
- Low call quality
- Low calendar event creation (few events per user per month)
- Device performance issues (high packet loss, high latency, poor video quality)
- Declining usage (fewer logins and calls over time)

### Phase 2 — Gather data via data_agent
Transfer to data_agent with clear, specific natural language questions. Be precise
about metrics, time periods, comparisons, and aggregations. Ask multiple questions
as needed and process each result before moving on.

Good examples:
- "Which customers have significantly fewer calendar events per licensed user than
  their segment average over the past 30 days?"
- "Show the week-over-week login trend for all customers over the past 7 weeks,
  highlighting any with a consistent decline."
- "Which customers have the highest percentage of devices with average video quality
  scores below 3.5?"

After receiving data results, summarize the findings and identify which customers
have discrete engagement issues that warrant intervention.

### Phase 3 — Create interventions via intervention_agent
For EACH customer with an identified engagement issue, transfer to intervention_agent
with a structured request. Do this one customer at a time. Include:
- customer_id and customer_name
- Problem profile (a short label like "Low Adoption" or "Poor Video Quality")
- A description of the problem with specific data points from Phase 2
- 3 key engagement metrics with values and units

Good examples:
- "Create an intervention for customer_id='pinnacle-fin', customer_name='Pinnacle
  Financial Group'. Problem profile: Low Adoption. Only 25% of licensed users are
  logging in regularly (login rate ~5 logins/user/month vs. enterprise baseline of
  18). Engagement metrics: login_rate=5.1/user/month, active_user_pct=25%,
  licensed_users=1800."

- "Create an intervention for customer_id='coastal-log', customer_name='Coastal
  Logistics Inc.'. Problem profile: Poor Video Quality. Telemetry across all 35
  rooms shows significant network-related degradation since a recent office
  relocation. Engagement metrics: packet_loss=4.0%, network_latency=94.9ms,
  video_quality=2.2/5.0."

The intervention_agent will search best-practice documentation, generate a branded
PDF, upload it to Cloud Storage, and return a summary with the document URL.

### Phase 4 — Present results
After all interventions are created, present a final summary to the user:
- List each customer, the issue identified, and the link to their intervention PDF.
- Note any patterns across customers or follow-up actions.

## Hard Rules
- NEVER write SQL, reference table/column names, or query databases yourself.
- NEVER write recommendations, intervention plans, or proposed actions yourself —
  that is the intervention_agent's job.
- NEVER generate PDFs or upload files.
- If you find yourself writing bullet points of recommendations for a customer,
  STOP and transfer to intervention_agent instead.
"""


# --- Improve Engagement agent agent ---
root_agent = LlmAgent(
    model=Gemini3(model="gemini-3-flash-preview"),
    name="improve_engagement_agent",
    description=(
        "Cymbal Meet Customer Engagement Improve Engagement agent. Interprets user "
        "requests about customer engagement, delegates data queries to "
        "specialized agents, and presents actionable insights."
    ),
    instruction=IMPROVE_ENGAGEMENT_INSTRUCTION,
    sub_agents=[data_agent, intervention_agent],
)
