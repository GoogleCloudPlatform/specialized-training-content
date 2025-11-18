#!/usr/bin/env bash
set -euo pipefail
if [[ -f env.rc ]]; then source env.rc; fi
read -p "Delete memory collection from Firestore? (y/N): " ans
if [[ "$ans" == "y" ]]; then
  gcloud firestore documents delete memory --project=$PROJECT_ID --quiet || true
fi
echo "Teardown complete."
