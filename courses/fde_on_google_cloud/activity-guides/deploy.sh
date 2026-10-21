#!/usr/bin/env bash
# Deploy the activity guide site to Cloud Run.
#
# Usage: ./deploy.sh PROJECT_ID [REGION]
#   REGION defaults to us-central1.
#   Set SERVICE to change the Cloud Run service name (default: fde-activity-guides).
set -euo pipefail

PROJECT_ID="${1:?Usage: ./deploy.sh PROJECT_ID [REGION]}"
REGION="${2:-us-central1}"
SERVICE="${SERVICE:-fde-activity-guides}"

cd "$(dirname "$0")"

echo "Regenerating HTML from Markdown..."
python3 build/md2html.py 0*.md instructor-activity-guide.md

echo "Enabling required APIs in $PROJECT_ID..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com \
  --project "$PROJECT_ID"

echo "Building and deploying $SERVICE to $REGION..."
gcloud run deploy "$SERVICE" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --source . \
  --allow-unauthenticated \
  --memory 256Mi \
  --max-instances 3 \
  --quiet

URL="$(gcloud run services describe "$SERVICE" --project "$PROJECT_ID" --region "$REGION" \
  --format 'value(status.url)')"

echo
echo "Share with the class:   $URL"
echo "Instructor guide:       $URL/instructor-activity-guide   (keep this private)"
