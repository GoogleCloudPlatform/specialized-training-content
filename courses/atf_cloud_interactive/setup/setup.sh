#!/usr/bin/env bash
# setup.sh — Phase 1 infrastructure provisioning for Cymbal Meet Agent System
#
# Provisions: APIs, service accounts, IAM roles, GCS buckets.
# Idempotent — safe to re-run.
#
# Usage:
#   ./setup.sh                     # uses gcloud's current project
#   PROJECT_ID=my-project ./setup.sh  # explicit project

set -euo pipefail

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PROJECT_ID="${PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"
REGION="${REGION:-us-central1}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "ERROR: No project set. Run 'gcloud config set project <id>' or export PROJECT_ID."
  exit 1
fi

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
echo " Project:  $PROJECT_ID ($PROJECT_NUMBER)"
echo " Region:   $REGION"
echo "============================================"
echo ""

# ---------------------------------------------------------------------------
# Phase 1a — Enable APIs
# ---------------------------------------------------------------------------
echo ">>> Enabling APIs..."

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

# ---------------------------------------------------------------------------
# Phase 1b — Service accounts
# ---------------------------------------------------------------------------
echo ">>> Creating service accounts..."

# Helper: create SA if it doesn't already exist
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
# Phase 1c — IAM roles
# ---------------------------------------------------------------------------
echo ">>> Granting IAM roles..."

# Agent SA roles (PRD section 6.3)
AGENT_ROLES=(
  "roles/bigquery.dataViewer"
  "roles/bigquery.jobUser"
  "roles/storage.objectAdmin"
  "roles/aiplatform.user"
  "roles/discoveryengine.editor"
  "roles/run.invoker"
)

for role in "${AGENT_ROLES[@]}"; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${AGENT_SA_EMAIL}" \
    --role="$role" \
    --condition=None \
    --quiet &>/dev/null
  echo "    $AGENT_SA  ← $role"
done

# GCS MCP SA roles
MCP_ROLES=(
  "roles/storage.objectAdmin"
)

for role in "${MCP_ROLES[@]}"; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${MCP_SA_EMAIL}" \
    --role="$role" \
    --condition=None \
    --quiet &>/dev/null
  echo "    $MCP_SA  ← $role"
done

echo ""

# ---------------------------------------------------------------------------
# Phase 1d — GCS buckets
# ---------------------------------------------------------------------------
echo ">>> Creating GCS buckets..."

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

# Interventions bucket needs public read for PDF URLs (PRD requirement)
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

check "APIs enabled (aiplatform)" \
  "gcloud services list --enabled --project=$PROJECT_ID --filter='name:aiplatform.googleapis.com' --format='value(name)' | grep -q aiplatform"

check "BigQuery MCP enabled" \
  "gcloud beta services mcp list --project=$PROJECT_ID 2>/dev/null | grep -q bigquery"

check "Agent SA exists ($AGENT_SA_EMAIL)" \
  "gcloud iam service-accounts describe $AGENT_SA_EMAIL --project=$PROJECT_ID"

check "MCP SA exists ($MCP_SA_EMAIL)" \
  "gcloud iam service-accounts describe $MCP_SA_EMAIL --project=$PROJECT_ID"

check "Staging bucket exists ($STAGING_BUCKET)" \
  "gsutil ls -b $STAGING_BUCKET"

check "Refs bucket exists ($REFS_BUCKET)" \
  "gsutil ls -b $REFS_BUCKET"

check "Interventions bucket exists ($INTERVENTIONS_BUCKET)" \
  "gsutil ls -b $INTERVENTIONS_BUCKET"

echo ""
echo "  Results: $PASS passed, $FAIL failed"
echo ""

if [[ $FAIL -gt 0 ]]; then
  echo "WARNING: Some checks failed. Review the output above."
  exit 1
fi

echo "Phase 1 setup complete."
echo ""

# ---------------------------------------------------------------------------
# Phase 2 — Python virtual environment & setup scripts
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/.venv"

echo ">>> Creating Python virtual environment..."
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

echo ">>> Converting markdown reference docs to PDF..."
bash "$SCRIPT_DIR/convert_md_to_pdf.sh"
echo ""

echo ">>> Uploading reference docs to GCS..."
"$VENV_DIR/bin/python" "$SCRIPT_DIR/upload_reference_docs.py"
echo ""

echo ">>> Creating Vertex AI Search datastore..."
"$VENV_DIR/bin/python" "$SCRIPT_DIR/create_datastore.py"
echo ""

echo "============================================"
echo " All setup steps complete!"
echo "============================================"
echo ""
echo "NOTE: Vertex AI Search requires ToS acceptance at:"
echo "  https://console.cloud.google.com/gen-app-builder?project=$PROJECT_ID"
