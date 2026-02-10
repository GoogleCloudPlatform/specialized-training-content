from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types
from google.adk.tools import google_search  # The Google Search tool

import os
import google.auth

_, project_id = google.auth.default()
os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
os.environ["GOOGLE_CLOUD_LOCATION"] = "global"
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"


root_agent = Agent(
    name="google_search_agent",
    description="Answer questions using Google Search.",
    model="gemini-2.5-flash-lite",
    instruction="You are an expert researcher. You stick to the facts.",
    # tools: functions to enhance the model's capabilities.
    tools=[google_search]
)

app = App(root_agent=root_agent, name="app")
