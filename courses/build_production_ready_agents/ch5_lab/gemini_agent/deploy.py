import os

import vertexai
from agent import app
from dotenv import load_dotenv
from vertexai import agent_engines

load_dotenv()

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
GOOGLE_CLOUD_STAGING_BUCKET = os.getenv("GOOGLE_CLOUD_STAGING_BUCKET", "")

vertexai.init(
    project=GOOGLE_CLOUD_PROJECT,
    location=GOOGLE_CLOUD_LOCATION,
    staging_bucket=GOOGLE_CLOUD_STAGING_BUCKET
)

remote_agent = agent_engines.create(
    agent_engine=app,
    display_name="GCP Tutorial Agent",
    requirements=["google-cloud-aiplatform[agent_engines,adk]"],
    # staging_bucket parameter may not be needed or use gcs_dir_name instead
)