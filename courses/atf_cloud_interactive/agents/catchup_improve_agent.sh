#!/bin/bash
# catchup_improve_agent.sh — Deploys the improve engagement agent solution for
# students who need to skip Task 3.
#
# This script:
#   1. Deletes any existing Agent Engine engines (avoids conflicts from failed deploys)
#   2. Copies the completed agent.py from agents_solution/improve_engagement_agent/
#   3. Creates a virtual environment and installs dependencies
#   4. Generates .env.deploy from .env.deploy.example with correct values
#   5. Generates .agent_engine_config.json from template with correct service account
#   6. Deploys the improve engagement agent to Agent Engine
#   7-11. Sets up Gemini Enterprise application with the deployed agent
#
# Prerequisites:
#   - gcloud CLI authenticated and configured with the lab project
#   - setup.sh has already been run (infrastructure is provisioned)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AGENT_DIR="${SCRIPT_DIR}/improve_engagement_agent"
SOLUTION_DIR="$(cd "${SCRIPT_DIR}/../agents_solution/improve_engagement_agent" && pwd)"

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

echo "============================================"
echo "Improve Engagement Agent Catchup Deployment"
echo "============================================"
echo "Project:         ${GOOGLE_CLOUD_PROJECT}"
echo "Project Number:  ${PROJECT_NUMBER}"
echo "Region:          ${GOOGLE_CLOUD_LOCATION}"
echo "============================================"

# --- Step 1: Delete existing Agent Engine engines ---
echo ""
echo "Step 1: Checking for existing Agent Engine engines ..."

ACCESS_TOKEN="$(gcloud auth print-access-token 2>/dev/null)"
BASE_URL="https://${GOOGLE_CLOUD_LOCATION}-aiplatform.googleapis.com/v1"
PARENT="projects/${GOOGLE_CLOUD_PROJECT}/locations/${GOOGLE_CLOUD_LOCATION}"

ENGINES_JSON="$(curl -s -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  "${BASE_URL}/${PARENT}/reasoningEngines")"

ENGINE_NAMES="$(echo "${ENGINES_JSON}" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for e in data.get('reasoningEngines', []):
    print(e['name'])
" 2>/dev/null || true)"

if [[ -z "${ENGINE_NAMES}" ]]; then
  echo "  No existing engines found."
else
  echo "  Found existing engines. Deleting ..."
  while IFS= read -r engine_name; do
    echo "    Deleting ${engine_name} ..."
    del_resp="$(curl -s -o /dev/null -w "%{http_code}" -X DELETE \
      -H "Authorization: Bearer ${ACCESS_TOKEN}" \
      "${BASE_URL}/${engine_name}?force=true")"
    if [[ "${del_resp}" == "200" ]]; then
      echo "      Deleted."
    else
      echo "      WARNING: Delete returned HTTP ${del_resp}. Continuing anyway."
    fi
  done <<< "${ENGINE_NAMES}"
  echo "  Done."
fi

# --- Step 2: Copy solution agent.py ---
echo ""
echo "Step 2: Copying solution agent.py ..."
cp "${SOLUTION_DIR}/agent.py" "${AGENT_DIR}/agent.py"
echo "  Done."

# --- Step 3: Create virtual environment and install dependencies ---
echo ""
echo "Step 3: Creating virtual environment and installing dependencies ..."
cd "${SCRIPT_DIR}"
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
echo "  Done."

# --- Step 4: Generate .env.deploy ---
echo ""
echo "Step 4: Generating .env.deploy ..."
sed -e "s|<YOUR_PROJECT_ID>|${GOOGLE_CLOUD_PROJECT}|g" \
    -e "s|<YOUR_PROJECT_NUMBER>|${PROJECT_NUMBER}|g" \
  "${AGENT_DIR}/.env.deploy.example" > "${AGENT_DIR}/.env.deploy"
echo "  Done."

# --- Step 5: Generate .agent_engine_config.json ---
echo ""
echo "Step 5: Generating .agent_engine_config.json ..."
sed "s|<YOUR_PROJECT_ID>|${GOOGLE_CLOUD_PROJECT}|g" \
  "${AGENT_DIR}/.agent_engine_config.json.template" > "${AGENT_DIR}/.agent_engine_config.json"
echo "  Done."

# --- Step 6: Deploy to Agent Engine ---
echo ""
echo "Step 6: Deploying improve engagement agent to Agent Engine ..."
unset GOOGLE_APPLICATION_CREDENTIALS 2>/dev/null || true
cd "${SCRIPT_DIR}"
bash deploy_improve_agent_to_agent_engine.sh

# --- Find the deployed reasoning engine ---
echo ""
echo "Finding deployed reasoning engine ..."

ACCESS_TOKEN="$(gcloud auth print-access-token 2>/dev/null)"
BASE_URL="https://${GOOGLE_CLOUD_LOCATION}-aiplatform.googleapis.com/v1"
PARENT="projects/${GOOGLE_CLOUD_PROJECT}/locations/${GOOGLE_CLOUD_LOCATION}"

REASONING_ENGINE_NAME="$(curl -s -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  "${BASE_URL}/${PARENT}/reasoningEngines" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for e in data.get('reasoningEngines', []):
    if e.get('displayName') == 'Improve Engagement Agent':
        print(e['name'])
        break
" 2>/dev/null)"

if [[ -z "${REASONING_ENGINE_NAME}" ]]; then
  echo "ERROR: Could not find reasoning engine with display name 'Improve Engagement Agent'."
  exit 1
fi
echo "  Found: ${REASONING_ENGINE_NAME}"

# --- Steps 7-11: Set up Gemini Enterprise application ---
cd "${SCRIPT_DIR}"
python3 setup_gemini_enterprise.py \
  "${GOOGLE_CLOUD_PROJECT}" \
  "${PROJECT_NUMBER}" \
  "${REASONING_ENGINE_NAME}"

echo ""
echo "============================================"
echo "Catchup complete!"
echo "  - Improve engagement agent deployed to Agent Engine"
echo "  - Gemini Enterprise application configured"
echo "============================================"
