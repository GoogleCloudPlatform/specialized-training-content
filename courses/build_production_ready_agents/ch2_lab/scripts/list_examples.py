"""
List all examples in an Example Store instance.
"""

import os
import sys

import vertexai
from google.api_core.client_options import ClientOptions
from google.cloud import aiplatform_v1beta1

GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "my-gcp-project")
GOOGLE_CLOUD_LOCATION = os.getenv("AGENT_ENGINE_LOCATION", "us-central1")
EXAMPLE_STORE_NAME = os.getenv("EXAMPLE_STORE_NAME", "")

def list_examples():    
    client_options = ClientOptions(
        api_endpoint=f"{GOOGLE_CLOUD_LOCATION}-aiplatform.googleapis.com"
    )

    client = aiplatform_v1beta1.ExampleStoreServiceClient(client_options=client_options)

    request = aiplatform_v1beta1.FetchExamplesRequest(
        example_store=EXAMPLE_STORE_NAME,
    )

    page_result = client.fetch_examples(request=request)

    # Handle the response
    for response in page_result:
        print(response)

if __name__ == "__main__":
    list_examples()
