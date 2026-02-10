import asyncio
import os

import vertexai
from google.adk.sessions import VertexAiSessionService

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "my-gcp-project")
GOOGLE_CLOUD_LOCATION = "us-central1"

def setup_agent_engine():
  client = vertexai.Client(
    project=GOOGLE_CLOUD_PROJECT,
    location=GOOGLE_CLOUD_LOCATION
  )

  # If you don't have an Agent Engine instance already, create an instance.
  agent_engine = client.agent_engines.create()
  return agent_engine

  # Print the agent engine ID, you will need it in the later steps to initialize
  # the ADK `VertexAiSessionService`.

async def prime_session_service(agent_engine):
    session_service = VertexAiSessionService(project=GOOGLE_CLOUD_PROJECT, location=GOOGLE_CLOUD_LOCATION)

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
    print(f"Your agent engine ID is: {agent_engine.api_resource.name}")
    asyncio.run(prime_session_service(agent_engine))