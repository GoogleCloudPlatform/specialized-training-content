"""
Deploy the Data Agent to Agent Engine (Vertex AI).

Usage:
    # Set your project first
    export GOOGLE_CLOUD_PROJECT=your-project-id

    # Deploy (uses gs://PROJECT-agent-staging by default)
    python deploy_data_agent.py

    # Deploy with a custom staging bucket
    python deploy_data_agent.py --staging-bucket gs://my-bucket

    # Output: projects/PROJECT/locations/us-central1/reasoningEngines/RESOURCE_ID
"""

import argparse
import os
import sys

import vertexai
from agent import app
from vertexai import agent_engines


def deploy(project_id: str, staging_bucket: str) -> str:
    """Deploy the Data Agent and return the resource name."""
    vertexai.init(
        project=project_id,
        location="us-central1",
        staging_bucket=staging_bucket,
    )

    print(f"Deploying Data Agent to project={project_id} ...")
    print(f"  staging bucket : {staging_bucket}")
    print(f"  location       : us-central1")
    print()

    agent_engine = agent_engines.create(
        agent_engine=app,
        requirements=[
            "google-adk",
            "google-auth",
            "google-cloud-bigquery",
            "google-genai",
        ],
        extra_packages=[os.path.dirname(os.path.abspath(__file__))],
        display_name="cymbal-meet-data-agent",
        description=(
            "Cymbal Meet data domain expert — translates natural language "
            "to BigQuery SQL via MCP."
        ),
    )

    resource_name = agent_engine.resource_name
    print()
    print("Deployment complete!")
    print(f"  Resource name: {resource_name}")
    print()
    print("Save this resource name — you'll need it for testing and for the")
    print("Orchestrator's A2A connection later.")
    return resource_name


def main():
    parser = argparse.ArgumentParser(
        description="Deploy the Cymbal Meet Data Agent to Agent Engine."
    )
    parser.add_argument(
        "--staging-bucket",
        default=None,
        help=(
            "GCS staging bucket (default: gs://PROJECT_ID-agent-staging). "
            "Must already exist."
        ),
    )
    args = parser.parse_args()

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print("ERROR: GOOGLE_CLOUD_PROJECT environment variable is not set.")
        print("  export GOOGLE_CLOUD_PROJECT=your-project-id")
        sys.exit(1)

    staging_bucket = args.staging_bucket or f"gs://{project_id}-agent-staging"
    deploy(project_id, staging_bucket)


if __name__ == "__main__":
    main()
