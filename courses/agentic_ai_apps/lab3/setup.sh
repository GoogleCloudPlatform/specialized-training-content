#!/usr/bin/env bash
set -euo pipefail

REGION="us-central1"
ZONE="us-central1-a"
NB_NAME="llm-notebook"

PROJECT_ID="$(gcloud config get-value project)"
if [[ -z "$PROJECT_ID" || "$PROJECT_ID" == "(unset)" ]]; then
  echo "No project set"; exit 1
fi

BUCKET="${PROJECT_ID}-llmquery-$(date +%s)"
gsutil mb -c STANDARD -l $REGION gs://$BUCKET/

gcloud services enable   aiplatform.googleapis.com   notebooks.googleapis.com   compute.googleapis.com   storage.googleapis.com   iamcredentials.googleapis.com

cat > env.rc <<EOF
export PROJECT_ID=$PROJECT_ID
export REGION=$REGION
export ZONE=$ZONE
export NB_NAME=$NB_NAME
export BUCKET=$BUCKET
EOF

gsutil cp env.rc gs://$BUCKET/env.rc
echo "Setup complete. Project: $PROJECT_ID  Bucket: $BUCKET"
