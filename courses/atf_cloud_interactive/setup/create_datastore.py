#!/usr/bin/env python3
"""create_datastore.py — Create Vertex AI Search datastore and import reference docs.

Creates an unstructured-document datastore in Vertex AI Search (Discovery Engine),
imports reference docs from GCS, and polls until indexing completes.
Idempotent — safe to re-run (skips datastore creation if it already exists,
re-import uses FULL reconciliation mode).

Prerequisites:
  - setup.sh has been run (APIs enabled, buckets created, AI Applications provisioned)
  - upload_reference_docs.py has been run (docs in GCS)

Usage:
  python setup/create_datastore.py                                       # defaults
  DATASTORE_ID=my-ds PROJECT_ID=my-project python setup/create_datastore.py
"""

import os
import subprocess
import sys

from google.api_core.exceptions import AlreadyExists, NotFound
from google.cloud import discoveryengine

DATASTORE_ID = os.environ.get("DATASTORE_ID", "cymbal-meet-docs")
DATASTORE_DISPLAY_NAME = "Cymbal Meet Reference Docs"
LOCATION = "global"


def get_project_id() -> str:
    project_id = os.environ.get("PROJECT_ID")
    if not project_id:
        result = subprocess.run(
            ["gcloud", "config", "get-value", "project"],
            capture_output=True, text=True,
        )
        project_id = result.stdout.strip()
    if not project_id:
        print("ERROR: No project set. Run 'gcloud config set project <id>' or export PROJECT_ID.")
        sys.exit(1)
    return project_id


def datastore_exists(ds_client: discoveryengine.DataStoreServiceClient,
                     project_id: str) -> bool:
    name = ds_client.data_store_path(
        project=project_id,
        location=LOCATION,
        data_store=DATASTORE_ID,
    )
    try:
        ds_client.get_data_store(name=name)
        return True
    except NotFound:
        return False


def create_datastore(ds_client: discoveryengine.DataStoreServiceClient,
                     project_id: str) -> None:
    parent = ds_client.collection_path(
        project=project_id,
        location=LOCATION,
        collection="default_collection",
    )
    data_store = discoveryengine.DataStore(
        display_name=DATASTORE_DISPLAY_NAME,
        industry_vertical=discoveryengine.IndustryVertical.GENERIC,
        solution_types=[discoveryengine.SolutionType.SOLUTION_TYPE_SEARCH],
        content_config=discoveryengine.DataStore.ContentConfig.CONTENT_REQUIRED,
    )
    request = discoveryengine.CreateDataStoreRequest(
        parent=parent,
        data_store_id=DATASTORE_ID,
        data_store=data_store,
    )
    try:
        operation = ds_client.create_data_store(request=request)
        print("    Waiting for datastore creation...")
        operation.result()
        print("    Datastore created.")
    except AlreadyExists:
        print("    Datastore already exists — skipping creation.")


def import_documents(doc_client: discoveryengine.DocumentServiceClient,
                     project_id: str) -> None:
    bucket_name = f"{project_id}-cymbal-meet-refs"
    parent = doc_client.branch_path(
        project=project_id,
        location=LOCATION,
        data_store=DATASTORE_ID,
        branch="default_branch",
    )
    request = discoveryengine.ImportDocumentsRequest(
        parent=parent,
        gcs_source=discoveryengine.GcsSource(
            input_uris=[f"gs://{bucket_name}/*"],
            data_schema="content",
        ),
        reconciliation_mode=discoveryengine.ImportDocumentsRequest.ReconciliationMode.FULL,
    )
    operation = doc_client.import_documents(request=request)
    print(f"    Import started. Operation: {operation.operation.name}")
    print("    Waiting for import and indexing to complete...")
    response = operation.result()
    metadata = discoveryengine.ImportDocumentsMetadata(operation.metadata)
    print(f"    Import complete. {metadata}")


def validate_datastore(ds_client: discoveryengine.DataStoreServiceClient,
                       project_id: str) -> bool:
    name = ds_client.data_store_path(
        project=project_id,
        location=LOCATION,
        data_store=DATASTORE_ID,
    )
    try:
        ds_client.get_data_store(name=name)
        return True
    except NotFound:
        return False


def main():
    project_id = get_project_id()

    print("=" * 48)
    print(" Vertex AI Search — Datastore Setup")
    print("=" * 48)
    print(f" Project:    {project_id}")
    print(f" Datastore:  {DATASTORE_ID}")
    print(f" Source:     gs://{project_id}-cymbal-meet-refs/*")
    print("=" * 48)
    print()

    ds_client = discoveryengine.DataStoreServiceClient()
    doc_client = discoveryengine.DocumentServiceClient()

    # Step 1 — Create datastore
    print(">>> Creating datastore...")
    if datastore_exists(ds_client, project_id):
        print("    Datastore already exists — skipping creation.")
    else:
        create_datastore(ds_client, project_id)
    print()

    # Step 2 — Import documents
    print(">>> Importing documents from GCS...")
    import_documents(doc_client, project_id)
    print()

    # Validation
    print("Validation:")
    if validate_datastore(ds_client, project_id):
        print(f"  [PASS] Datastore '{DATASTORE_ID}' exists and is accessible")
    else:
        print(f"  [FAIL] Datastore '{DATASTORE_ID}' not found")
        sys.exit(1)

    print()
    print("Vertex AI Search setup complete.")
    print()
    print("The Intervention Agent can now use this datastore with:")
    print()
    print("  from google.adk.tools import VertexAiSearchTool")
    print()
    print(f'  vertex_search_tool = VertexAiSearchTool(')
    print(f'      data_store_id="projects/{project_id}/locations/{LOCATION}'
          f'/collections/default_collection/dataStores/{DATASTORE_ID}"')
    print(f'  )')
    print()


if __name__ == "__main__":
    main()
