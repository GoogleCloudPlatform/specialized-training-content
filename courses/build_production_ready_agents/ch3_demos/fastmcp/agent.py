import os

from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import \
    StreamableHTTPConnectionParams

root_agent = Agent(
    model='gemini-3.5-flash',
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
                url='http://127.0.0.1:8001/mcp'),
            # Without this, only the server's tools are exposed to the agent;
            # this adds a load_mcp_resource tool so it can read api_docs too.
            use_mcp_resources=True,
        )
    ],
)