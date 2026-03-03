#!/bin/bash

export GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-$(gcloud config get-value project)}"
export GOOGLE_CLOUD_LOCATION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
export AGENT_SA="${AGENT_SA:-cymbal-agent}"
export AGENT_SERVICE_NAME="intervention-agent"

# Ensure VS_DATASTORE_ID is set
if [ -z "$VS_DATASTORE_ID" ]; then
    echo "ERROR: VS_DATASTORE_ID must be set as an environment variable"
    echo "Example: export VS_DATASTORE_ID='your-datastore-id-here'"
    exit 1
fi

gcloud run deploy $AGENT_SERVICE_NAME \
    --port=8080 \
    --source=. \
    --no-allow-unauthenticated \
    --region="$GOOGLE_CLOUD_LOCATION" \
    --project=$GOOGLE_CLOUD_PROJECT \
    --service-account $AGENT_SA \
    --set-env-vars=\
GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,\
GOOGLE_CLOUD_LOCATION=$GOOGLE_CLOUD_LOCATION,\
VS_DATASTORE_ID=$VS_DATASTORE_ID,\
GCS_MCP_ENDPOINT=$GCS_MCP_ENDPOINT,\
INTERVENTIONS_BUCKET=$INTERVENTIONS_BUCKET,\
GOOGLE_GENAI_USE_VERTEXAI=true,\
OTEL_SERVICE_NAME=$AGENT_SERVICE_NAME,\
OTEL_PYTHON_LOGGING_AUTO_INSTRUMENTATION_ENABLED=true,\
ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false,\
OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT=true

echo "Deployment complete!"
echo "Service URL:"
gcloud run services describe $AGENT_SERVICE_NAME --region=$GOOGLE_CLOUD_LOCATION --project=$GOOGLE_CLOUD_PROJECT --format='value(status.url)'
