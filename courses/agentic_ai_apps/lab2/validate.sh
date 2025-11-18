#!/usr/bin/env bash
set -euo pipefail
TASK=${1:-all}
source env.rc

pass(){ echo "✅ Task $1 PASSED"; }
fail(){ echo "❌ Task $1 FAILED: $2"; exit 1; }

check1(){
  gcloud services list --enabled | grep -q firestore || fail 1 "Firestore not enabled"
  pass 1
}

check2(){
  gcloud firestore databases list --format="value(name)" | grep -q "(default)" || fail 2 "Firestore not initialized"
  pass 2
}

check3(){
  gsutil ls "gs://${PROJECT_ID}-memory*/memory_summary.json" >/dev/null 2>&1 || fail 3 "Memory summary file missing"
  pass 3
}

case $TASK in
  1) check1;;
  2) check2;;
  3) check3;;
  all) check1; check2; check3;;
esac
