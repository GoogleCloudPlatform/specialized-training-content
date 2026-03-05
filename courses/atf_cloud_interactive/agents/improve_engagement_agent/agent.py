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
from google.adk.tools.agent_tool import AgentTool
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

data_tool = AgentTool(agent=data_agent)
intervention_tool = AgentTool(agent=intervention_agent)

# --- Improve Engagement agent system prompt ---
IMPROVE_ENGAGEMENT_INSTRUCTION = """\
## Overview
You are the Cymbal Meet Improve Engagement Agent. You help customer success teams
identify product engagement issues and create intervention documents to address them.

You have two tools:
- **data_tool**: Queries BigQuery. Use this tool for ALL data questions.
- **intervention_tool**: Generates branded PDF intervention documents and uploads
  them to Cloud Storage. Use this tool for ALL intervention creation.


## Casual conversation
- You may engage in casual conversation with the user, but steer towards
  gathering data and creating interventions. The ultimate goal is to get
  actionable insights and create intervention documents.

## Workflow

Follow these phases in order. Complete each phase before starting the next.

### Phase 1 — Interpret the request
Determine what data is needed based on the user's question:
- If the user asks about a particular customer, focus on that customer's data and
  compare against their segment and overall averages.
- If the user asks about a segment, look for engagement issues across ALL customers
  in that segment, checking EVERY issue category below.
- If the user asks about a specific category of issues (e.g. video quality), focus
  on that category across relevant customers. Do not attempt to discover/address
  other types of issues not mentioned by the user.
- Otherwise, scan for ALL of the engagement issue categories below across all customers.

There are 5 engagement issue categories. When the request is broad (a whole
segment, "all issues", "engagement issues", etc.) you MUST check ALL of these:
1. Low login adoption (low % of licensed users logging in monthly)
2. Low call quality (poor audio/video quality scores)
3. Low calendar event creation (few events per user per month)
4. Device performance issues (high packet loss, high latency, poor video quality)
5. Declining usage (fewer logins and calls over time compared to previous periods)

Do NOT cherry-pick a subset — if the user's request covers multiple categories,
you must investigate every applicable one.

### Phase 2 — Gather data via data_tool
Compose a comprehensive data request that covers ALL applicable engagement issue
categories from Phase 1, then send it to the data_tool.

**Time frame**: If the user specifies a time period, use it. If no time frame is
mentioned, default to the **last 90 days** of data. Always include the time frame
explicitly in your request to the data_tool.

**Critical: Do NOT invent numeric thresholds.** Never specify absolute cutoffs like
"below 50%" or "below 3.5". Instead, ask the data_tool to compare each customer's
metrics against their segment average and identify customers performing significantly
below average. The data_tool knows how to determine statistical significance — let
it do that work.

Your request to data_tool should:
- Explicitly list every engagement metric category you need checked
- Ask for each customer's values AND segment averages side by side
- Ask the data_tool to flag customers significantly underperforming their segment
- Specify which segment(s) to analyze if the user mentioned one
- Be precise about time periods and aggregations

Example — for a broad request covering all issue types, you would send:
"For all customers, compare each customer's engagement metrics against their
segment average and identify customers significantly underperforming. Check all
of the following: (1) login adoption rate (% licensed users logging in monthly),
(2) call quality scores, (3) calendar events per user per month, (4) device
performance (packet loss, latency, video quality), (5) usage trends over time
(login and call volume changes). For each flagged customer, include customer_id,
company_name, segment, the customer's metric values, and the segment averages."

You may need to transfer multiple times to ask follow-up data questions.

The data_agent only returns raw data and summaries — it does NOT create
interventions, recommendations, or action plans. If its response includes
recommendations, ignore them and use only the data.

After receiving data results, analyze the findings yourself and identify which
customers have discrete engagement issues that warrant intervention.

**Checkpoint before moving to Phase 3:** Review which of the 5 issue categories
you investigated. If the user's request was broad and you have not yet checked all
5 categories, send additional data requests before proceeding.

### Phase 3 — Create interventions via intervention_tool
For EACH identified engagement issue, compose a structured
intervention request, and send it to the intervention_tool.
Do this one issue at a time. Your text must include:
- customer_id and customer_name
- Problem profile (a short label like "Low Adoption" or "Poor Video Quality")
- A description of the problem with specific data points from Phase 2
- 3 key engagement metrics with values and units

Example — you would generate this summary and send to the tool:
"Create an intervention for customer_id='coastal-log', customer_name='Coastal
Logistics Inc.'. Problem profile: Poor Video Quality. Telemetry across all 35
rooms shows significant network-related degradation since a recent office
relocation. Engagement metrics: packet_loss=4.0%, network_latency=94.9ms,
video_quality=2.2/5.0."

The intervention_tool will search best-practice documentation, generate a branded
PDF, upload it to Cloud Storage, and return a summary with the document URL.

### Phase 4 — Present results
After all interventions are created, present a final summary to the user:
- List each customer, the issue identified, and the link to their intervention PDF.
- Note any patterns across customers or follow-up actions.

## Hard Rules
- NEVER write SQL, reference table/column names, or query databases yourself.
- NEVER specify absolute numeric thresholds (e.g. "below 50%", "below 3.5") in
  data requests. Always ask data_tool to compare against segment averages.
- NEVER write recommendations, intervention plans, or proposed actions yourself —
  that is the intervention_tool's job.
- NEVER generate PDFs or upload files.
- NEVER skip engagement issue categories when the user's request is broad. If the
  request covers a segment or "all issues", you must check all 5 categories.
- If you find yourself writing bullet points of recommendations for a customer,
  STOP — compose an intervention request and transfer to intervention_tool instead.
- ALWAYS output a specific request as text BEFORE every transfer. Never transfer
  with only the user's original message as context.
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
    tools=[data_tool, intervention_tool],
)
