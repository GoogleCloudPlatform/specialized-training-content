#!/bin/bash
# catchup.sh — Deploys the data agent solution for students who need to skip Task 1.
#
# This script:
#   1. Creates a virtual environment and installs dependencies
#   2. Copies the completed agent.py from agents_solution/data_agent/
#   3. Generates .env from .env.example with the correct project ID
#   4. Generates agent_card.json with the correct Cloud Run service URL
#   5. Deploys the data agent to Cloud Run
#
# Prerequisites:
#   - gcloud CLI authenticated and configured with the lab project
#   - setup.sh has already been run (infrastructure is provisioned)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOLUTION_DIR="$(cd "${SCRIPT_DIR}/../../agents_solution/data_agent" && pwd)"

# --- Derive environment variables ---
GOOGLE_CLOUD_PROJECT="$(gcloud config get-value project 2>/dev/null)"
if [[ -z "${GOOGLE_CLOUD_PROJECT}" ]]; then
  echo "ERROR: No active gcloud project. Run: gcloud config set project <PROJECT_ID>"
  exit 1
fi

PROJECT_NUMBER="$(gcloud projects describe "${GOOGLE_CLOUD_PROJECT}" \
  --format='value(projectNumber)' 2>/dev/null)"
if [[ -z "${PROJECT_NUMBER}" ]]; then
  echo "ERROR: Could not retrieve project number for ${GOOGLE_CLOUD_PROJECT}."
  exit 1
fi

export GOOGLE_CLOUD_PROJECT
export GOOGLE_CLOUD_LOCATION="us-central1"
export MODEL_ARMOR_LOCATION="us"
export AGENT_SA="cymbal-agent@${GOOGLE_CLOUD_PROJECT}.iam.gserviceaccount.com"
export AGENT_SERVICE_NAME="data-agent"

SERVICE_URL="https://${AGENT_SERVICE_NAME}-${PROJECT_NUMBER}.${GOOGLE_CLOUD_LOCATION}.run.app"

echo "============================================"
echo "Data Agent Catchup Deployment"
echo "============================================"
echo "Project:         ${GOOGLE_CLOUD_PROJECT}"
echo "Project Number:  ${PROJECT_NUMBER}"
echo "Region:          ${GOOGLE_CLOUD_LOCATION}"
echo "Service Account: ${AGENT_SA}"
echo "Service Name:    ${AGENT_SERVICE_NAME}"
echo "Service URL:     ${SERVICE_URL}"
echo "============================================"

# --- Step 1: Create virtual environment and install dependencies ---
echo ""
echo "Step 1: Creating virtual environment and installing dependencies ..."
cd "${SCRIPT_DIR}"
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
echo "  Done."

# --- Step 2: Copy solution agent.py ---
echo ""
echo "Step 2: Copying solution agent.py ..."
cp "${SOLUTION_DIR}/agent.py" "${SCRIPT_DIR}/agent.py"
echo "  Done."

# --- Step 3: Generate .env from .env.example ---
echo ""
echo "Step 3: Generating .env file ..."
sed "s|<YOUR_PROJECT_ID>|${GOOGLE_CLOUD_PROJECT}|g" \
  "${SCRIPT_DIR}/.env.example" > "${SCRIPT_DIR}/.env"
echo "  Done."

# --- Step 4: Generate agent_card.json from template ---
echo ""
echo "Step 4: Generating agent_card.json with service URL ..."
sed "s|http://localhost:8080|${SERVICE_URL}|" \
  "${SCRIPT_DIR}/agent_card.json.template" > "${SCRIPT_DIR}/agent_card.json"
echo "  Done."

# --- Step 5: Deploy to Cloud Run ---
echo ""
echo "Step 5: Deploying data agent to Cloud Run ..."
cd "${SCRIPT_DIR}"
bash deploy_to_run.sh

echo ""
echo "============================================"
echo "Catchup complete! Data agent deployed to:"
echo "  ${SERVICE_URL}"
echo "============================================"
