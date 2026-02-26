"""
Deploy the Data Agent to Agent Engine from source files.

Unlike deploy.py (which serializes the agent object and requires a GCS
staging bucket), this script sends the raw source files to Agent Engine
and lets the service build the container.  This is better suited for
CI/CD pipelines and does NOT require a Cloud Storage bucket.

Reference:
    https://docs.cloud.google.com/agent-builder/agent-engine/deploy#from-source-files

Usage:
    # Set your project first
    export GOOGLE_CLOUD_PROJECT=your-project-id

    # Deploy
    python deploy_from_source.py

    # Output: projects/PROJECT/locations/us-central1/reasoningEngines/RESOURCE_ID
"""

import argparse
import os
import sys

import vertexai


def deploy(project_id: str) -> str:
    """Deploy the Data Agent from source and return the resource name."""
    client = vertexai.Client(project=project_id, location="us-central1")

    agent_dir = os.path.dirname(os.path.abspath(__file__))
    agents_dir = os.path.dirname(agent_dir)
    requirements_file = "data_agent/requirements.txt"

    print(f"Deploying Data Agent (from source) to project={project_id} ...")
    print(f"  source dir     : {agents_dir}")
    print(f"  requirements   : {requirements_file}")
    print(f"  location       : us-central1")
    print()

    original_cwd = os.getcwd()
    try:
        os.chdir(agents_dir)
        agent_engine = client.agent_engines.create(
            config={
                "display_name": "cymbal-meet-data-agent-1",
                "description": (
                    "Cymbal Meet data domain expert — translates natural language "
                    "to BigQuery SQL via MCP."
                ),
                "source_packages": ["data_agent"],
                "entrypoint_module": "data_agent.agent",
                "entrypoint_object": "app",
                "requirements_file": requirements_file,
                "class_methods": [
                    {
                        "name": "async_stream_query",
                        "api_mode": "stream",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "user_id": {"type": "string"},
                                "session_id": {"type": "string"},
                                "message": {"type": "string"},
                            },
                            "required": ["user_id", "message"],
                        },
                    },
                    {
                        "name": "async_create_session",
                        "api_mode": "",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "user_id": {"type": "string"},
                            },
                            "required": ["user_id"],
                        },
                    },
                    {
                        "name": "async_list_sessions",
                        "api_mode": "",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "user_id": {"type": "string"},
                            },
                            "required": ["user_id"],
                        },
                    },
                    {
                        "name": "async_get_session",
                        "api_mode": "",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "user_id": {"type": "string"},
                                "session_id": {"type": "string"},
                            },
                            "required": ["user_id", "session_id"],
                        },
                    },
                    {
                        "name": "async_delete_session",
                        "api_mode": "",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "user_id": {"type": "string"},
                                "session_id": {"type": "string"},
                            },
                            "required": ["user_id", "session_id"],
                        },
                    },
                ],
            },
        )
    finally:
        os.chdir(original_cwd)

    resource_name = agent_engine.api_resource.name
    print()
    print("Deployment complete!")
    print(f"  Resource name: {resource_name}")
    print()
    print("Save this resource name — you'll need it for testing and for the")
    print("Orchestrator's A2A connection later.")
    return resource_name


def main():
    parser = argparse.ArgumentParser(
        description="Deploy the Cymbal Meet Data Agent to Agent Engine (from source)."
    )
    parser.parse_args()

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print("ERROR: GOOGLE_CLOUD_PROJECT environment variable is not set.")
        print("  export GOOGLE_CLOUD_PROJECT=your-project-id")
        sys.exit(1)

    deploy(project_id)


if __name__ == "__main__":
    main()
