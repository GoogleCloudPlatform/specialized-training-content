#!/usr/bin/env bash
# deploy_gcs_mcp.sh — Build and deploy the GCS MCP server to Cloud Run
#
# Deploys a custom Python FastMCP server (wrapping google-cloud-storage)
# to Cloud Run with Streamable HTTP transport, then grants the agent SA
# permission to invoke it.
#
# Prerequisites:
#   - setup.sh has been run (APIs enabled, service accounts created)
#   - gcloud CLI authenticated with sufficient permissions
#
# Usage:
#   ./deploy_gcs_mcp.sh                        # uses gcloud's current project
#   PROJECT_ID=my-project ./deploy_gcs_mcp.sh  # explicit project

# set -euo pipefail

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${REGION:-us-central1}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "ERROR: No project set. Run 'gcloud config set project <id>' or export PROJECT_ID."
  exit 1
fi

SERVICE_NAME="gcs-mcp-server"
MCP_SA_EMAIL="gcs-mcp-sa@${PROJECT_ID}.iam.gserviceaccount.com"
AGENT_SA_EMAIL="cymbal-agent@${PROJECT_ID}.iam.gserviceaccount.com"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="${SCRIPT_DIR}/gcs-mcp-server"

echo "============================================"
echo " GCS MCP Server — Cloud Run Deployment"
echo "============================================"
echo " Project:  $PROJECT_ID"
echo " Region:   $REGION"
echo " Service:  $SERVICE_NAME"
echo " SA:       $MCP_SA_EMAIL"
echo " Source:   $SOURCE_DIR"
echo "============================================"
echo ""

# ---------------------------------------------------------------------------
# Step 1 — Deploy to Cloud Run (source-based build)
# ---------------------------------------------------------------------------
echo ">>> Deploying $SERVICE_NAME to Cloud Run..."
echo "    This builds the container via Cloud Build and deploys it."
echo ""

gcloud run deploy "$SERVICE_NAME" \
  --source "$SOURCE_DIR" \
  --service-account="$MCP_SA_EMAIL" \
  --no-allow-unauthenticated \
  --ingress=all \
  --region="$REGION" \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=3 \
  --timeout=300 \
  --project="$PROJECT_ID" \
  --quiet

echo ""
echo "    Deployed."
echo ""

# ---------------------------------------------------------------------------
# Step 2 — Grant agent SA invoker access
# ---------------------------------------------------------------------------
echo ">>> Granting $AGENT_SA_EMAIL invoker access on $SERVICE_NAME..."

gcloud run services add-iam-policy-binding "$SERVICE_NAME" \
  --region="$REGION" \
  --member="serviceAccount:${AGENT_SA_EMAIL}" \
  --role="roles/run.invoker" \
  --project="$PROJECT_ID" \
  --quiet

echo "    Granted."
echo ""

# ---------------------------------------------------------------------------
# Step 3 — Retrieve and display the service URL
# ---------------------------------------------------------------------------
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --format="value(status.url)")

MCP_ENDPOINT="${SERVICE_URL}/mcp"

echo "============================================"
echo " Deployment complete"
echo "============================================"
echo " Service URL:  $SERVICE_URL"
echo " MCP endpoint: $MCP_ENDPOINT"
echo ""
echo " Use this MCP endpoint in the Intervention Agent config:"
echo ""
echo "   GCS_MCP_URL=$MCP_ENDPOINT"
echo ""
echo " Test with MCP Inspector:"
echo ""
echo "   gcloud run services proxy $SERVICE_NAME --region=$REGION &"
echo "   npx @modelcontextprotocol/inspector --transport streamablehttp --server-url http://localhost:8080/mcp"
echo ""
echo " Verify the service is running:"
echo ""
echo "   gcloud run services describe $SERVICE_NAME --region=$REGION --format='value(status.conditions[0].status)'"
echo ""
