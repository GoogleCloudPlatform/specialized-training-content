#!/usr/bin/env bash
set -euo pipefail
TASK=${1:-all}
if [[ ! -f env.rc ]]; then echo "env.rc missing. Run ./setup.sh"; exit 1; fi
source env.rc

pass(){ echo "✅ Task $1 PASSED"; }
fail(){ echo "❌ Task $1 FAILED: $2"; exit 1; }

check1(){ gsutil ls gs://$BUCKET/ >/dev/null || fail 1 "Bucket missing"; pass 1; }
check2(){
  gcloud notebooks instances list --location=$ZONE --format="value(name)" | grep -q $NB_NAME     || fail 2 "Notebook instance '$NB_NAME' not found in $ZONE"
  pass 2
}
check3(){
  gsutil ls gs://$BUCKET/agent_runs/latest/success.json >/dev/null     || fail 3 "Success marker not found at gs://$BUCKET/agent_runs/latest/success.json"
  pass 3
}

case $TASK in
  1) check1;;
  2) check2;;
  3) check3;;
  all) check1; check2; check3;;
esac
