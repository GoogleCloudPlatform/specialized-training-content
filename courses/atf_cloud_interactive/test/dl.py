#!/usr/bin/env python3
"""List Vertex AI Search datastores in the current GCP project.

Usage:
    python list_datastores.py
    python list_datastores.py --project my-project-id
"""

import argparse
import os
import sys

from google.cloud import discoveryengine_v1


def list_datastores(project_id: str = None, location: str = "global") -> None:
    """List all Vertex AI Search datastores in the project.

    Args:
        project_id: GCP project ID. If None, uses GOOGLE_CLOUD_PROJECT env var or gcloud config.
        location: GCP region (default: global - required by Vertex AI Search)
    """
    if project_id is None:
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            try:
                import subprocess
                result = subprocess.run(
                    ["gcloud", "config", "get-value", "project"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                project_id = result.stdout.strip()
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("ERROR: Could not determine project ID.", file=sys.stderr)
                print("Set GOOGLE_CLOUD_PROJECT or run: gcloud config set project <PROJECT_ID>", file=sys.stderr)
                sys.exit(1)

    print(f"Listing Vertex AI Search datastores in project '{project_id}' (location: {location})...\n")

    try:
        client = discoveryengine_v1.DataStoreServiceClient()
        parent = f"projects/{project_id}/locations/{location}"
        request = discoveryengine_v1.ListDataStoresRequest(parent=parent)
        response = client.list_data_stores(request=request)

        datastores = list(response)

        if not datastores:
            print("No datastores found.")
            return

        print(f"Found {len(datastores)} datastore(s):\n")
        for i, datastore in enumerate(datastores, 1):
            print(f"{i}. {datastore.display_name}")
            print(f"   Resource Name: {datastore.name}")
            # Extract just the ID from the resource name
            datastore_id = datastore.name.split("/")[-1]
            print(f"   Datastore ID: {datastore_id}")
            if hasattr(datastore, 'create_time') and datastore.create_time:
                print(f"   Created: {datastore.create_time}")
            print()

    except Exception as e:
        print(f"ERROR: Failed to list datastores: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="List Vertex AI Search datastores in a GCP project"
    )
    parser.add_argument(
        "--project",
        help="GCP project ID (default: GOOGLE_CLOUD_PROJECT env var or gcloud config)",
    )
    parser.add_argument(
        "--location",
        default="global",
        help="GCP region (default: global - required by Vertex AI Search)",
    )

    args = parser.parse_args()
    list_datastores(project_id=args.project, location=args.location)
