#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="$(gcloud config get-value project)"
REGION="us-central1"

gcloud services enable aiplatform.googleapis.com firestore.googleapis.com storage.googleapis.com

cat > env.rc <<EOF
export PROJECT_ID=$PROJECT_ID
export REGION=$REGION
EOF

echo "Setup complete. Firestore and Vertex AI APIs enabled."
