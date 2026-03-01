#!/usr/bin/env python3
"""upload_reference_docs.py — Upload reference docs to GCS for Vertex AI Search ingestion.

Uploads all markdown files from reference_docs/ to the refs GCS bucket.
Idempotent — re-running overwrites existing objects.

Prerequisites:
  - setup.sh has been run (refs bucket exists)
  - gcloud CLI authenticated

Usage:
  python setup/upload_reference_docs.py                        # uses gcloud's current project
  PROJECT_ID=my-project python setup/upload_reference_docs.py  # explicit project
"""

import os
import subprocess
import sys
from pathlib import Path

from google.cloud import storage


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


def main():
    project_id = get_project_id()
    bucket_name = f"{project_id}-cymbal-meet-refs"

    # Locate reference_docs/ relative to this script
    script_dir = Path(__file__).resolve().parent
    docs_dir = script_dir.parent / "reference_docs"

    if not docs_dir.is_dir():
        print(f"ERROR: Reference docs directory not found: {docs_dir}")
        sys.exit(1)

    doc_files = sorted(docs_dir.glob("*.md"))
    if not doc_files:
        print(f"ERROR: No .md files found in {docs_dir}")
        sys.exit(1)

    print("=" * 48)
    print(" Upload Reference Docs to GCS")
    print("=" * 48)
    print(f" Project:  {project_id}")
    print(f" Bucket:   gs://{bucket_name}")
    print(f" Docs dir: {docs_dir}")
    print(f" Files:    {len(doc_files)}")
    print("=" * 48)
    print()

    client = storage.Client(project=project_id)
    bucket = client.bucket(bucket_name)

    for doc_path in doc_files:
        blob_name = doc_path.name
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(str(doc_path), content_type="text/plain")
        print(f"  Uploaded {blob_name} ({doc_path.stat().st_size:,} bytes)")

    # Validation — list objects and confirm count
    print()
    print("Validation:")
    blobs = list(client.list_blobs(bucket_name))
    md_blobs = [b for b in blobs if b.name.endswith(".md")]
    if len(md_blobs) >= len(doc_files):
        print(f"  [PASS] {len(md_blobs)} markdown files in gs://{bucket_name}")
    else:
        print(f"  [FAIL] Expected {len(doc_files)} files, found {len(md_blobs)}")
        sys.exit(1)

    print()
    print("Upload complete.")
    print()
    print("Next step:")
    print("  python setup/create_search_app.py")
    print()


if __name__ == "__main__":
    main()
