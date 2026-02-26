"""
Delete a deployed Data Agent from Agent Engine.

Usage:
    python teardown_agent.py \
        --resource-name projects/PROJECT/locations/us-central1/reasoningEngines/ID

    # Skip confirmation prompt
    python teardown_agent.py --resource-name ... --yes
"""

import argparse
import os
import sys

import vertexai
from vertexai import agent_engines


def delete_agent(resource_name: str, project_id: str):
    """Delete the deployed agent by resource name."""
    vertexai.init(project=project_id, location="us-central1")

    print(f"Deleting agent: {resource_name}")
    agent_engines.delete(resource_name, force=True)
    print("Done. Agent has been deleted.")


def main():
    parser = argparse.ArgumentParser(
        description="Delete a deployed Data Agent from Agent Engine.",
    )
    parser.add_argument(
        "--resource-name",
        required=True,
        help="Agent Engine resource name (projects/…/reasoningEngines/…)",
    )
    parser.add_argument(
        "--project",
        default=None,
        help="GCP project ID (default: GOOGLE_CLOUD_PROJECT env var)",
    )
    parser.add_argument(
        "--yes", "-y",
        action="store_true",
        help="Skip confirmation prompt",
    )
    args = parser.parse_args()

    project_id = args.project or os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print("ERROR: Provide --project or set GOOGLE_CLOUD_PROJECT.")
        sys.exit(1)

    if not args.yes:
        print(f"This will permanently delete the agent:")
        print(f"  {args.resource_name}")
        confirm = input("Continue? [y/N] ").strip().lower()
        if confirm != "y":
            print("Aborted.")
            sys.exit(0)

    delete_agent(args.resource_name, project_id)


if __name__ == "__main__":
    main()
