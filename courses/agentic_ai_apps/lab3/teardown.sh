#!/usr/bin/env bash
set -euo pipefail
if [[ -f env.rc ]]; then source env.rc; else echo "env.rc missing, using defaults"; REGION="us-central1"; ZONE="us-central1-a"; NB_NAME="llm-notebook"; fi

gcloud notebooks instances stop $NB_NAME --location=$ZONE --quiet || true
gcloud notebooks instances delete $NB_NAME --location=$ZONE --quiet || true
echo "Notebook deleted. Bucket gs://${BUCKET:-your-bucket} retained."
