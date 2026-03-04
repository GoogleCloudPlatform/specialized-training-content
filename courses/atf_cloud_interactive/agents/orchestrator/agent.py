"""Orchestrator agent — A2A client coordinating the Data Agent on Cloud Run.

Deploys to Agent Engine via `adk deploy agent_engine`. The Orchestrator is
NOT an A2A server — it is the user-facing agent that delegates data questions
to the Data Agent via its Cloud Run A2A endpoint.

Currently wired to the Data Agent only. The Intervention Agent will be
added later.
"""

import logging
import os
import warnings
from functools import cached_property

from dotenv import load_dotenv

load_dotenv()

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

# Suppress repetitive ADK experimental-feature warnings and noisy INFO logs
warnings.filterwarnings("ignore", message=r"\[EXPERIMENTAL\]")
logging.getLogger("google.adk").setLevel(logging.WARNING)
logging.getLogger("google.genai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

# --- Telemetry ---
_gcp_exporters = get_gcp_exporters(
    enable_cloud_tracing=True,
    enable_cloud_logging=True,
)
_gcp_resource = get_gcp_resource(project_id=PROJECT_ID)
maybe_set_otel_providers(
    otel_hooks_to_setup=[_gcp_exporters],
    otel_resource=_gcp_resource,
)


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
        "about customer engagement, translates to SQL, executes via BigQuery, "
        "and returns structured results. Delegate ALL data-related questions "
        "to this agent — never attempt to query data directly."
    ),
    agent_card=f"{DATA_AGENT_URL}/.well-known/agent.json",
    httpx_client=_data_agent_http,
)


# --- Orchestrator system prompt ---
ORCHESTRATOR_INSTRUCTION = """\
You are the Cymbal Meet Engagement Intervention Agent. You help customer
success teams identify product engagement issues, and create interventions
to address them, aiming to improve customer engagement with the Cymbal Meet
video conferencing platform.

## Your Role
You interpret user requests about customer engagement and coordinate with
specialized agents to fulfill them. You do NOT have direct access to data or
databases — you delegate data questions to the Data Agent, which handles all
BigQuery queries.

## Workflow
When the user asks about customer engagement data (login rates, call volumes,
device health, meeting frequency, usage trends, etc.):

1. **Interpret** the user's request and determine what data is needed.
2. **Delegate** by transferring to the data_agent with a clear, specific
   natural language question. Be precise about what metrics, time periods,
   comparisons, or aggregations you need. Examples of good delegation
   questions:
   - "Which customers have significantly fewer calendar events per licensed
     user than their segment average over the past 30 days?"
   - "Show the week-over-week login trend for all customers over the past
     7 weeks, highlighting any with a consistent decline."
   - "Which customers have the highest percentage of devices with average
     video quality scores below 3.5?"
3. **Present** the results to the user with clear formatting, context, and
   actionable insights.

## Guidelines
- Highlight notable patterns, outliers, or concerns in the data.
- When comparing customers, include relevant benchmarks or segment averages
  for context.
- Suggest follow-up questions or next steps when appropriate.
- Be concise but thorough — customer success teams need actionable insights.

## What You DON'T Do
- You NEVER compose SQL or reference table names, column names, or schemas.
- You NEVER access BigQuery or any database directly.
- You don't create intervention documents yet (that capability is coming soon).
"""


# --- Orchestrator agent ---
root_agent = LlmAgent(
    model=Gemini3(model="gemini-3-flash-preview"),
    name="orchestrator",
    description=(
        "Cymbal Meet Customer Engagement Orchestrator. Interprets user "
        "requests about customer engagement, delegates data queries to "
        "specialized agents, and presents actionable insights."
    ),
    instruction=ORCHESTRATOR_INSTRUCTION,
    sub_agents=[data_agent],
)
