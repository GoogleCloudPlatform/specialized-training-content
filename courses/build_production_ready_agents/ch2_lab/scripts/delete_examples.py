"""
Delete all examples from an Example Store instance.
"""

import os
import sys

import vertexai
from google.api_core.client_options import ClientOptions
from google.cloud import aiplatform_v1beta1

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "my-gcp-project")
GOOGLE_CLOUD_LOCATION = os.getenv("AGENT_ENGINE_LOCATION", "us-central1")
EXAMPLE_STORE_NAME = os.getenv("EXAMPLE_STORE_NAME", "")

def delete_examples():    
    client_options = ClientOptions(
        api_endpoint=f"{GOOGLE_CLOUD_LOCATION}-aiplatform.googleapis.com"
    )

    client = aiplatform_v1beta1.ExampleStoreServiceClient(client_options=client_options)

    # Step 1: Fetch all examples from the example store
    fetch_request = aiplatform_v1beta1.FetchExamplesRequest(
        example_store=EXAMPLE_STORE_NAME,
    )

    page_result = client.fetch_examples(request=fetch_request)

    # Step 2: Create a list of example_id properties
    example_ids = []
    for response in page_result:
        example_ids.append(response.example_id)
    
    if not example_ids:
        print("No examples found to delete.")
        return
    
    print(f"Found {len(example_ids)} examples to delete.")
    
    # Step 3 & 4: Create remove examples request and delete the examples
    request = aiplatform_v1beta1.RemoveExamplesRequest(
        example_store=EXAMPLE_STORE_NAME,
        example_ids=example_ids
    )
    
    response = client.remove_examples(request=request)
    print(f"Successfully deleted {len(example_ids)} examples.")
    print(response)

if __name__ == "__main__":
    delete_examples()
