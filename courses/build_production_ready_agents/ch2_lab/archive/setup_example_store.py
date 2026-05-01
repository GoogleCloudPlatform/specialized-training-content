"""
Create an Example Store instance for the ADK agent.

This script creates a new Example Store using the text-embedding-005 model
for similarity search of examples.
"""

import os
import sys

import vertexai
from vertexai.preview import example_stores

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "my-gcp-project")
GOOGLE_CLOUD_LOCATION = os.getenv("AGENT_ENGINE_LOCATION", "us-central1")
EMBEDDING_MODEL = "text-embedding-005"


def create_example_store():
    
    # Initialize Vertex AI
    vertexai.init(
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION
    )
    
    try:
        # Create the Example Store
        example_store = example_stores.ExampleStore.create(
            example_store_config=example_stores.ExampleStoreConfig(
                vertex_embedding_model=EMBEDDING_MODEL
            )
        )
        
        return example_store
        
    except Exception as e:
        print(f"✗ Error creating Example Store: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    example_store = create_example_store()
    # Print only the export command to stdout so it can be eval'd
    print(f"Line to add to .env: EXAMPLE_STORE_NAME={example_store.resource_name}")
    print(f"Command to run in terminal: export EXAMPLE_STORE_NAME={example_store.name}")
