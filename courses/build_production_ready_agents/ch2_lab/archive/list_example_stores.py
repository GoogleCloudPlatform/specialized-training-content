"""
List all Example Store instances in the current project.
"""

import os
import sys

import vertexai
from vertexai.preview import example_stores

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "my-gcp-project")
GOOGLE_CLOUD_LOCATION = os.getenv("AGENT_ENGINE_LOCATION", "us-central1")


def list_example_stores():
    """List all Example Store instances in the project."""
    
    # Initialize Vertex AI
    vertexai.init(
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION
    )
    
    try:
        # List all example stores
        stores = example_stores.ExampleStore.list()
        
        if not stores:
            print("No Example Store instances found.")
            return
        
        print(f"Found {len(stores)} Example Store instance(s):\n")
        
        for idx, store in enumerate(stores, 1):
            print(f"{idx}. {store.resource_name}")
            if hasattr(store, 'create_time'):
                print(f"   Created: {store.create_time}")
            print()
        
    except Exception as e:
        print(f"Error listing Example Stores: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    list_example_stores()
