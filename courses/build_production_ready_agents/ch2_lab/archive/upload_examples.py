"""
Upload example files to the Example Store.

This script reads example JSON files from the examples/ directory
and uploads them to the configured Example Store.
"""

import json
import os
import sys
from pathlib import Path

import vertexai
from google.genai import types as genai_types
from vertexai.preview import example_stores

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "my-gcp-project")
GOOGLE_CLOUD_LOCATION = os.getenv("AGENT_ENGINE_LOCATION", "us-central1")
EXAMPLE_STORE_NAME = os.getenv("EXAMPLE_STORE_NAME", "")
EXAMPLES_DIR = Path(__file__).parent / "examples"

print(f"Using Example Store: {EXAMPLE_STORE_NAME}")


def load_example_file(file_path: Path) -> dict:
    """Load an example from a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)


def upload_examples():
    """Upload all examples from the examples directory to the Example Store."""
    if not EXAMPLE_STORE_NAME:
        print("✗ Error: EXAMPLE_STORE_NAME not set in .env file")
        sys.exit(1)
    
    print(f"Connecting to Example Store: {EXAMPLE_STORE_NAME}")
    
    # Initialize Vertex AI
    vertexai.init(
        project=GOOGLE_CLOUD_PROJECT,
        location=GOOGLE_CLOUD_LOCATION
    )
    
    try:
        # Connect to the Example Store
        example_store = example_stores.ExampleStore(EXAMPLE_STORE_NAME)
        print("✓ Connected to Example Store")
    except Exception as e:
        print(f"✗ Error connecting to Example Store: {e}")
        sys.exit(1)
    
    # Find all JSON files in examples directory
    if not EXAMPLES_DIR.exists():
        print(f"✗ Error: Examples directory not found: {EXAMPLES_DIR}")
        sys.exit(1)
    
    example_files = list(EXAMPLES_DIR.glob("*.json"))
    
    if not example_files:
        print(f"No example files found in {EXAMPLES_DIR}")
        return
    
    print(f"\nFound {len(example_files)} example file(s)")
    
    # Upload examples (max 5 per request)
    batch_size = 5
    total_uploaded = 0
    
    for i in range(0, len(example_files), batch_size):
        batch = example_files[i:i + batch_size]
        examples_to_upload = []
        
        for file_path in batch:
            print(f"\nProcessing: {file_path.name}")
            
            try:
                example_data = load_example_file(file_path)
                examples_to_upload.append(example_data)
                print(f"  ✓ Loaded example from {file_path.name}")
            except Exception as e:
                print(f"  ✗ Error loading {file_path.name}: {e}")
                continue
        
        # Upload batch
        if examples_to_upload:
            try:
                print(f"\nUploading batch of {len(examples_to_upload)} examples...")
                example_store.upsert_examples(examples=examples_to_upload)
                total_uploaded += len(examples_to_upload)
                print(f"✓ Uploaded {len(examples_to_upload)} examples")
            except Exception as e:
                print(f"✗ Error uploading batch: {e}")
    
    print(f"\n{'='*60}")
    print(f"✓ Upload complete! Total examples uploaded: {total_uploaded}")
    print(f"{'='*60}")


if __name__ == "__main__":
    upload_examples()
