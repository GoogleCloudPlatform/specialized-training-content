import os

from fastapi.openapi.models import (OAuth2, OAuthFlowAuthorizationCode,
                                    OAuthFlows)
from google.adk.agents.llm_agent import Agent
from google.adk.auth.auth_credential import (AuthCredential,
                                             AuthCredentialTypes, OAuth2Auth)
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import \
    StreamableHTTPConnectionParams

root_agent = Agent(
    model='gemini-3-flash-preview',
    name='root_agent',
    description='Friendly helper agent.',
    instruction="""
    Greet the user. 
    File bugs using the create_support_ticket tool.
    Return docs using the api_docs resource.
    """,
    tools=[
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url='http://127.0.0.1:8000/mcp')
        )
    ],
)