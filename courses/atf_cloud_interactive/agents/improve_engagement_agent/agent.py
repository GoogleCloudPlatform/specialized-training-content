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

from .prompt_task3 import IMPROVE_ENGAGEMENT_INSTRUCTION

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
                retry_options=types.HttpRetryOptions(
                    max_delay=7,
                    exp_base=1.5,
                    jitter=.5,
                )
            ),
        )

# TODO CLOUD_RUN_AUTH: Create an httpx.Auth subclass for Cloud Run OIDC authentication.
# Steps:
#   1. Subclass httpx.Auth and accept an audience URL in __init__.
#   2. In auth_flow(), skip auth for localhost/127.0.0.1 requests (just yield the request).
#   3. For all other requests, fetch a Google OIDC identity token using
#      google.oauth2.id_token.fetch_id_token() with the audience URL.
#   4. Attach the token as a Bearer Authorization header and yield the request.


# TODO DATA_AGENT_CLIENT: Create an A2A client for the remote Data Agent.
# Steps:
#   1. Create an httpx.AsyncClient with _CloudRunAuth(DATA_AGENT_URL) and a 600s timeout.
#   2. Create a RemoteA2aAgent named "data_agent" with a description of its capabilities
#      (translates natural language to SQL, executes via BigQuery, returns structured results).
#   3. Point agent_card at the DATA_AGENT_URL's .well-known/agent.json endpoint.
#   4. Pass the httpx client to httpx_client.


# TODO INTERVENTION_AGENT_CLIENT: Create an A2A client for the remote Intervention Agent.
# Steps:
#   1. Create an httpx.AsyncClient with _CloudRunAuth(INTERVENTION_AGENT_URL) and a 600s timeout.
#   2. Create a RemoteA2aAgent named "intervention_agent" with a description of its capabilities
#      (accepts engagement data, searches best-practice content via Vertex AI Search,
#      generates personalized intervention PDFs uploaded to GCS).
#   3. Point agent_card at the INTERVENTION_AGENT_URL's .well-known/agent.json endpoint.
#   4. Pass the httpx client to httpx_client.

# TODO AGENT_TOOLS: Wrap each remote agent in an AgentTool for use by the root agent.
# Steps:
#   1. Create data_tool by wrapping data_agent with AgentTool.
#   2. Create intervention_tool by wrapping intervention_agent with AgentTool.

# --- Improve Engagement agent system prompt ---
# For Task 3 (data agent only), import from prompt_task3.
# For Task 4 (data + intervention agents), swap to prompt_task4.


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
    tools=[
        # TODO REGISTER_TOOLS: Pass data_tool here.
    ],
)
