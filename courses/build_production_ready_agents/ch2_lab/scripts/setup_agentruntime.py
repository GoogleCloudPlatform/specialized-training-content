import asyncio
import os

import vertexai
from google.adk.sessions import VertexAiSessionService
from dotenv import load_dotenv

load_dotenv()

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "my-gcp-project")
AGENT_RUNTIME_LOCATION = os.getenv("AGENT_RUNTIME_LOCATION", "us-central1")

def setup_agent_engine():
  client = vertexai.Client(
    project=GOOGLE_CLOUD_PROJECT,
    location=AGENT_RUNTIME_LOCATION
  ) # type: ignore

  # If you don't have an Agent Runtime deployment already, create one
  agent_engine = client.agent_engines.create(
    config={"display_name": "Gemini Cloud Tutor Runtime Deployment"}
  )
  return agent_engine

  # Print the Agent Runtime deployment (AgentEngine) ID, you will need it in the later steps to initialize
  # the ADK `VertexAiSessionService`.

async def prime_session_service(agent_engine):
    session_service = VertexAiSessionService(project=GOOGLE_CLOUD_PROJECT, location=AGENT_RUNTIME_LOCATION)

    # Create a dummy session to prime the service
    session = await session_service.create_session(
        app_name=agent_engine.api_resource.name,
        user_id="lab_user_1",
        state={}
    )
    session_id = session.id
    print(f"Created dummy session with ID: {session_id}")

if __name__ == "__main__":
    agent_engine = setup_agent_engine()
    print(f"Your Agent Runtime deployment ID is: {agent_engine.api_resource.name}")
    # asyncio.run(prime_session_service(agent_engine))