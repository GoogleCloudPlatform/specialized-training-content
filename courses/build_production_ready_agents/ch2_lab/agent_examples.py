from google.adk import Agent
from google.adk.tools import google_search
from utilities import GCP_SERVICE_REGIONS

# Create the agent with minimal base instruction
# Dynamic instructions will be added via examples in the server
root_agent = Agent(
    name="gemini_cloud_tutor_with_examples",
    model="gemini-2.5-flash-lite",
    instruction="""
    You're my cloud technology tutor, helping me develop a solid understanding of Google Cloud concepts and products.
    Use any examples provided to shape your responses.
    """
)
