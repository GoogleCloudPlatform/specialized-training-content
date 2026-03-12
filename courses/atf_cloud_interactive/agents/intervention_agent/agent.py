"""Intervention agent: RAG-backed PDF generation for customer engagement interventions.

This agent:
1. Accepts customer engagement data (customer_id, problem_profile, metrics)
2. Uses Vertex AI Search (RAG) to retrieve relevant troubleshooting content
3. Generates a branded PDF with recommendations using Jinja2 + WeasyPrint
4. Obtains a GCS signed upload URL via MCP, then uploads the PDF directly to GCS
"""

import logging
import os
import warnings
from functools import cached_property

import httpx
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
from google.adk.telemetry.google_cloud import (get_gcp_exporters,
                                               get_gcp_resource)
from google.adk.telemetry.setup import maybe_set_otel_providers
from google.adk.tools.mcp_tool.mcp_session_manager import \
    StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from google.adk.tools.vertex_ai_search_tool import VertexAiSearchTool
from google.genai import Client, types
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from pdf import generate_pdf_from_template
from prompt import INTERVENTION_AGENT_INSTRUCTION

# --- Environment configuration ---
PROJECT_ID = os.environ["GOOGLE_CLOUD_PROJECT"]
GCS_MCP_ENDPOINT = os.environ.get(
    "GCS_MCP_ENDPOINT",
    "https://gcs-mcp-server-PLACEHOLDER.us-central1.run.app/mcp"
)
VS_DATASTORE_ID = os.environ.get("VS_DATASTORE_ID", "")
INTERVENTIONS_BUCKET = os.environ.get("INTERVENTIONS_BUCKET", f"gs://{PROJECT_ID}-interventions")

# TODO GCS MCP SCOPES: Define the GCS MCP toolset scopes.
# Steps:
#   1. Create a GCS_MCP_SCOPES list with cloud-platform and devstorage.read_write scopes.

# Suppress repetitive ADK experimental-feature warnings and noisy INFO logs
warnings.filterwarnings("ignore", message=r"\[EXPERIMENTAL\]")
logging.getLogger("google.adk").setLevel(logging.WARNING)
logging.getLogger("google.genai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

_gcp_creds, _gcp_project = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"],
)
_gcp_exporters = get_gcp_exporters(
    enable_cloud_tracing=True,
    enable_cloud_logging=True,
    google_auth=(_gcp_creds, _gcp_project),
)
_gcp_resource = get_gcp_resource(project_id=PROJECT_ID)
maybe_set_otel_providers(
    otel_hooks_to_setup=[_gcp_exporters],
    otel_resource=_gcp_resource,
)


def _create_gcs_mcp_toolset() -> McpToolset:
    # TODO MCP TOOLSET: Create and return an McpToolset for GCS.
    # Steps:
    #   1. Set connection_params using StreamableHTTPConnectionParams with the GCS MCP endpoint URL.
    #   2. Set auth_scheme to OAuth2 with a clientCredentials flow pointing at Google's token URL.
    #   3. Set auth_credential to a SERVICE_ACCOUNT type using ADC (use_default_credential=True),
    #      with GCS_MCP_SCOPES, use_id_token=True, and audience set to the GCS MCP endpoint.
    pass


def upload_to_signed_url(
    signed_url: str,
    file_path: str,
    content_type: str = "application/pdf",
) -> dict:
    """Upload a local file to GCS using a pre-generated signed URL.

    HTTP PUTs the file bytes directly to GCS — no content passes through MCP.
    Call this after generate_upload_signed_url returns a signed_url.

    Args:
        signed_url: The signed URL from generate_upload_signed_url.
        file_path: Absolute path to the file to upload (e.g. from generate_pdf_from_template).
        content_type: MIME type — must match what was used to generate the signed URL.

    Returns:
        dict with success (bool) and bytes_uploaded (int).
    """
    with open(file_path, "rb") as f:
        data = f.read()
    response = httpx.put(
        signed_url,
        content=data,
        headers={
            "Content-Type": content_type,
            "Cache-Control": "no-cache, no-store, must-revalidate",
        },
    )
    response.raise_for_status()
    return {"success": True, "bytes_uploaded": len(data)}


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


# --- Agent definition ---
root_agent = LlmAgent(
    model=Gemini3(model="gemini-3-flash-preview"),
    name="intervention_agent",
    description=(
        "Cymbal Meet intervention specialist. Accepts customer engagement data, "
        "searches for relevant troubleshooting content via Vertex AI Search, "
        "and generates personalized intervention PDFs."
    ),
    instruction=INTERVENTION_AGENT_INSTRUCTION,
    tools=[
        VertexAiSearchTool(
            data_store_id=VS_DATASTORE_ID,
            bypass_multi_tools_limit=True,
        ),
        # TODO REGISTER_TOOLS: Add generate_pdf_from_template, upload_to_signed_url,
        #   and _create_gcs_mcp_toolset() here.
    ],
)

# TODO A2A APP: Create the A2A application using to_a2a().
# Steps:
#   1. Call to_a2a() with root_agent and agent_card="agent_card.json".
