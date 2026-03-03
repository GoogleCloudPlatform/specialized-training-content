#!/usr/bin/env bash
# setup.sh — Full infrastructure provisioning for Cymbal Meet Agent System
#
# Provisions: APIs, service accounts, IAM roles, GCS buckets,
#             reference doc upload, Vertex AI Search datastore,
#             BigQuery dataset + synthetic data.
# Idempotent — safe to re-run.
#
# Usage:
#   ./setup.sh                          # interactive prompt for project ID
#   PROJECT_ID=my-project ./setup.sh    # explicit project (skips prompt)

# set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
REGION="${REGION:-us-central1}"
DATASTORE_ID="${DATASTORE_ID:-cymbal-meet-docs}"

# Prompt for project ID if not set
if [[ -z "${PROJECT_ID:-}" ]]; then
  CURRENT_PROJECT=$(gcloud config get-value project 2>/dev/null || true)
  if [[ -n "$CURRENT_PROJECT" ]]; then
    read -rp "Enter GCP project ID [$CURRENT_PROJECT]: " INPUT_PROJECT
    PROJECT_ID="${INPUT_PROJECT:-$CURRENT_PROJECT}"
  else
    read -rp "Enter GCP project ID: " PROJECT_ID
  fi
fi

if [[ -z "$PROJECT_ID" ]]; then
  echo "ERROR: No project ID provided."
  exit 1
fi

# Configure gcloud to use this project
echo ">>> Configuring gcloud SDK..."
gcloud config set project "$PROJECT_ID" --quiet
gcloud auth application-default set-quota-project "$PROJECT_ID" 2>/dev/null || true
echo "    Project set to $PROJECT_ID"
echo ""

PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")

AGENT_SA="cymbal-agent"
AGENT_SA_EMAIL="${AGENT_SA}@${PROJECT_ID}.iam.gserviceaccount.com"

MCP_SA="gcs-mcp-sa"
MCP_SA_EMAIL="${MCP_SA}@${PROJECT_ID}.iam.gserviceaccount.com"

STAGING_BUCKET="gs://${PROJECT_ID}-agent-staging"
REFS_BUCKET="gs://${PROJECT_ID}-cymbal-meet-refs"
INTERVENTIONS_BUCKET="gs://${PROJECT_ID}-cymbal-meet-interventions"

echo "============================================"
echo " Cymbal Meet Agent System — Setup"
echo "============================================"
echo " Project:    $PROJECT_ID ($PROJECT_NUMBER)"
echo " Region:     $REGION"
echo " Datastore:  $DATASTORE_ID"
echo "============================================"
echo ""

# ---------------------------------------------------------------------------
# Phase 1 — Enable APIs
# ---------------------------------------------------------------------------
echo ">>> Phase 1: Enabling APIs..."

gcloud services enable \
  aiplatform.googleapis.com \
  discoveryengine.googleapis.com \
  bigquery.googleapis.com \
  run.googleapis.com \
  storage.googleapis.com \
  cloudbuild.googleapis.com \
  artifactregistry.googleapis.com \
  cloudresourcemanager.googleapis.com \
  logging.googleapis.com \
  monitoring.googleapis.com \
  compute.googleapis.com \
  iam.googleapis.com \
  --project="$PROJECT_ID" \
  --quiet

echo "    APIs enabled."
echo ""

# Enable BigQuery MCP endpoint (separate from the regular API enablement)
echo ">>> Enabling BigQuery MCP endpoint..."
gcloud beta services mcp enable bigquery.googleapis.com \
  --project="$PROJECT_ID" \
  --quiet 2>/dev/null || true
echo "    BigQuery MCP enabled."
echo ""

echo ""
echo ">>> Granting MCP Tool User role to agent service account..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
  --member="serviceAccount:${AGENT_SA_EMAIL}" \
  --role="roles/mcp.toolUser" \
  --quiet
echo ""

# ---------------------------------------------------------------------------
# Phase 2 — Service accounts
# ---------------------------------------------------------------------------
echo ">>> Phase 2: Creating service accounts..."

create_sa_if_missing() {
  local sa_name="$1"
  local display="$2"
  if gcloud iam service-accounts describe "${sa_name}@${PROJECT_ID}.iam.gserviceaccount.com" \
       --project="$PROJECT_ID" &>/dev/null; then
    echo "    $sa_name already exists — skipping."
  else
    gcloud iam service-accounts create "$sa_name" \
      --display-name="$display" \
      --project="$PROJECT_ID" \
      --quiet
    echo "    Created $sa_name."
  fi
}

create_sa_if_missing "$AGENT_SA" "Cymbal Meet Agent SA"
create_sa_if_missing "$MCP_SA"   "GCS MCP Server SA"
echo ""

# ---------------------------------------------------------------------------
# Phase 3 — IAM roles
# ---------------------------------------------------------------------------
echo ">>> Phase 3: Granting IAM roles..."

AGENT_ROLES=(
  "roles/bigquery.dataViewer"
  "roles/bigquery.jobUser"
  "roles/storage.objectAdmin"
  "roles/aiplatform.user"
  "roles/discoveryengine.editor"
  "roles/run.invoker"
  "roles/cloudtelemetry.metricsWriter"
  "roles/cloudtelemetry.tracesWriter"
  "roles/logging.logWriter"
  "roles/monitoring.metricWriter"
  "roles/serviceusage.serviceUsageAdmin"
)

for role in "${AGENT_ROLES[@]}"; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${AGENT_SA_EMAIL}" \
    --role="$role" \
    --condition=None \
    --quiet &>/dev/null
  echo "    $AGENT_SA  <- $role"
done

MCP_ROLES=(
  "roles/storage.objectAdmin"
)

for role in "${MCP_ROLES[@]}"; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${MCP_SA_EMAIL}" \
    --role="$role" \
    --condition=None \
    --quiet &>/dev/null
  echo "    $MCP_SA  <- $role"
done

echo ""

# ---------------------------------------------------------------------------
# Phase 4 — GCS buckets
# ---------------------------------------------------------------------------
echo ">>> Phase 4: Creating GCS buckets..."

create_bucket_if_missing() {
  local bucket="$1"
  local extra_flags="${2:-}"
  if gsutil ls -b "$bucket" &>/dev/null; then
    echo "    $bucket already exists — skipping."
  else
    gsutil mb -l "$REGION" -p "$PROJECT_ID" $extra_flags "$bucket"
    echo "    Created $bucket"
  fi
}

create_bucket_if_missing "$STAGING_BUCKET" "-b on"
create_bucket_if_missing "$REFS_BUCKET" "-b on"
create_bucket_if_missing "$INTERVENTIONS_BUCKET" "-b on"

# Interventions bucket needs public read for PDF URLs
echo "    Setting public read on interventions bucket..."
gsutil iam ch allUsers:objectViewer "$INTERVENTIONS_BUCKET" 2>/dev/null || true

# Provision Discovery Engine service agent and grant read access to refs bucket
echo "    Provisioning Discovery Engine service agent..."
gcloud beta services identity create \
  --service=discoveryengine.googleapis.com \
  --project="$PROJECT_ID" \
  --quiet 2>/dev/null || true
DISCOVERY_SA="service-${PROJECT_NUMBER}@gcp-sa-discoveryengine.iam.gserviceaccount.com"
echo "    Granting Discovery Engine access to refs bucket..."
gsutil iam ch "serviceAccount:${DISCOVERY_SA}:objectAdmin" "$REFS_BUCKET" 2>/dev/null || true
gsutil iam ch "serviceAccount:${DISCOVERY_SA}:objectViewer" "$REFS_BUCKET" 2>/dev/null || true
echo ""

# ---------------------------------------------------------------------------
# Phase 5 — Python environment & reference docs
# ---------------------------------------------------------------------------
VENV_DIR="$SCRIPT_DIR/.venv"

echo ">>> Phase 5: Setting up Python environment..."
if [[ -d "$VENV_DIR" ]]; then
  echo "    $VENV_DIR already exists — skipping creation."
else
  python3 -m venv "$VENV_DIR"
  echo "    Created $VENV_DIR"
fi

echo ">>> Installing Python dependencies..."
"$VENV_DIR/bin/pip" install --quiet --upgrade pip
"$VENV_DIR/bin/pip" install --quiet -r "$SCRIPT_DIR/requirements.txt"
echo "    Dependencies installed."
echo ""

echo ">>> Uploading reference docs to GCS..."
"$VENV_DIR/bin/python" "$SCRIPT_DIR/upload_reference_docs.py"
echo ""

# ---------------------------------------------------------------------------
# Phase 6 — Provision AI Applications & create Vertex AI Search datastore
# ---------------------------------------------------------------------------
echo ">>> Phase 6: Provisioning AI Applications (Discovery Engine)..."
curl -s -X POST \
  "https://discoveryengine.googleapis.com/v1/projects/${PROJECT_ID}:provision" \
  -H "Authorization: Bearer $(gcloud auth print-access-token)" \
  -H "Content-Type: application/json" \
  -d '{
    "acceptDataUseTerms": true,
    "dataUseTermsVersion": "2022-11-23"
  }' | head -c 500
echo ""
echo "    AI Applications provisioned."
echo ""

echo ">>> Creating Vertex AI Search datastore..."
DATASTORE_ID="$DATASTORE_ID" "$VENV_DIR/bin/python" "$SCRIPT_DIR/create_datastore.py"
echo ""

# ---------------------------------------------------------------------------
# Phase 7 — BigQuery dataset & synthetic data
# ---------------------------------------------------------------------------
echo ">>> Phase 7: Creating BigQuery tables and loading synthetic data..."
"$VENV_DIR/bin/python" "$SCRIPT_DIR/generate_data.py"
echo ""

# ---------------------------------------------------------------------------
# Phase 8 — Deploy GCS MCP server to Cloud Run
# ---------------------------------------------------------------------------
echo ">>> Phase 8: Deploying GCS MCP server to Cloud Run..."

SERVICE_NAME="gcs-mcp-server"
SOURCE_DIR="${SCRIPT_DIR}/gcs-mcp-server"

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

echo ">>> Granting $AGENT_SA_EMAIL invoker access on $SERVICE_NAME..."

gcloud run services add-iam-policy-binding "$SERVICE_NAME" \
  --region="$REGION" \
  --member="serviceAccount:${AGENT_SA_EMAIL}" \
  --role="roles/run.invoker" \
  --project="$PROJECT_ID" \
  --quiet

echo "    Granted."
echo ""

# Grant MCP SA permission to sign its own tokens (required for V4 signed URL generation)
echo ">>> Granting $MCP_SA_EMAIL token creator on itself (for signed URL generation)..."

gcloud iam service-accounts add-iam-policy-binding "$MCP_SA_EMAIL" \
  --member="serviceAccount:${MCP_SA_EMAIL}" \
  --role="roles/iam.serviceAccountTokenCreator" \
  --project="$PROJECT_ID" \
  --condition=None

echo "    Granted."
echo ""

SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
  --region="$REGION" \
  --project="$PROJECT_ID" \
  --format="value(status.url)")

MCP_ENDPOINT="${SERVICE_URL}/mcp"
echo "    MCP endpoint: $MCP_ENDPOINT"
echo ""

# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
echo "============================================"
echo " Validation"
echo "============================================"
PASS=0
FAIL=0

check() {
  local label="$1"
  local cmd="$2"
  if eval "$cmd" &>/dev/null; then
    echo "  [PASS] $label"
    ((PASS++))
  else
    echo "  [FAIL] $label"
    ((FAIL++))
  fi
}

# APIs
check "APIs enabled (aiplatform)" \
  "gcloud services list --enabled --project=$PROJECT_ID --filter='name:aiplatform.googleapis.com' --format='value(name)' | grep -q aiplatform"

check "BigQuery MCP enabled" \
  "gcloud beta services mcp list --project=$PROJECT_ID 2>/dev/null | grep -q bigquery"

# Service accounts
check "Agent SA exists ($AGENT_SA_EMAIL)" \
  "gcloud iam service-accounts describe $AGENT_SA_EMAIL --project=$PROJECT_ID"

check "MCP SA exists ($MCP_SA_EMAIL)" \
  "gcloud iam service-accounts describe $MCP_SA_EMAIL --project=$PROJECT_ID"

# GCS buckets
check "Staging bucket exists ($STAGING_BUCKET)" \
  "gsutil ls -b $STAGING_BUCKET"

check "Refs bucket exists ($REFS_BUCKET)" \
  "gsutil ls -b $REFS_BUCKET"

check "Interventions bucket exists ($INTERVENTIONS_BUCKET)" \
  "gsutil ls -b $INTERVENTIONS_BUCKET"

# Reference docs in GCS
check "Reference docs uploaded to GCS" \
  "gsutil ls ${REFS_BUCKET}/*.pdf 2>/dev/null | grep -q .pdf"

# BigQuery
check "BigQuery dataset exists (cymbal_meet)" \
  "bq show --project_id=$PROJECT_ID cymbal_meet"

check "BigQuery table: customers" \
  "bq show --project_id=$PROJECT_ID cymbal_meet.customers"

check "BigQuery table: logins" \
  "bq show --project_id=$PROJECT_ID cymbal_meet.logins"

check "BigQuery table: calendar_events" \
  "bq show --project_id=$PROJECT_ID cymbal_meet.calendar_events"

check "BigQuery table: device_telemetry" \
  "bq show --project_id=$PROJECT_ID cymbal_meet.device_telemetry"

check "BigQuery table: calls" \
  "bq show --project_id=$PROJECT_ID cymbal_meet.calls"

# Cloud Run
check "GCS MCP server deployed ($SERVICE_NAME)" \
  "gcloud run services describe $SERVICE_NAME --region=$REGION --project=$PROJECT_ID"

echo ""
echo "  Results: $PASS passed, $FAIL failed"
echo ""

if [[ $FAIL -gt 0 ]]; then
  echo "WARNING: Some checks failed. Review the output above."
  exit 1
fi

echo "============================================"
echo " All setup complete!"
echo "============================================"
echo ""
echo "GCS MCP endpoint: $MCP_ENDPOINT"
echo ""
echo "Next steps:"
echo "  1. Test data agent locally: cd agents/data_agent && adk web"
echo ""