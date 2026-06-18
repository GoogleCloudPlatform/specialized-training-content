#!/usr/bin/env bash
#
# prep.sh — one-time token substitution for the Cymbal landing-zone lab.
#
# This is the ONLY script in the lab. Run it once, right after cloning, BEFORE
# any `kubectl apply`. It rewrites the project-ID / region tokens
# (${CLICKSTREAM_PROJECT_ID}, ${PORTAL_PROJECT_ID}, ${BUILD_PROJECT_ID},
# ${REGION}) in place, so every later `kubectl apply` uses plain, ready
# manifests. After it runs the tokens are consumed and no later step touches
# envsubst.
#
# To start over: re-clone, or `git checkout -- templates/ day2/` to restore the
# raw tokens.
#
# Usage:
#   export CLICKSTREAM_PROJECT_ID=... PORTAL_PROJECT_ID=... BUILD_PROJECT_ID=... REGION=us-central1
#   ./prep.sh
set -euo pipefail

# --- Require every token's variable to be set (REGION may default). ----------
: "${REGION:=us-central1}"
export REGION

missing=()
for var in CLICKSTREAM_PROJECT_ID PORTAL_PROJECT_ID BUILD_PROJECT_ID; do
  if [ -z "${!var:-}" ]; then
    missing+=("$var")
  fi
done
if [ "${#missing[@]}" -ne 0 ]; then
  echo "ERROR: the following required environment variables are not set:" >&2
  printf '  - %s\n' "${missing[@]}" >&2
  echo >&2
  echo "Export them first, e.g.:" >&2
  echo "  export CLICKSTREAM_PROJECT_ID=qwiklabs-gcp-01-... \\" >&2
  echo "         PORTAL_PROJECT_ID=qwiklabs-gcp-02-... \\" >&2
  echo "         BUILD_PROJECT_ID=qwiklabs-gcp-03-... \\" >&2
  echo "         REGION=us-central1" >&2
  exit 1
fi

# --- envsubst must be available (provided by gettext). -----------------------
if ! command -v envsubst >/dev/null 2>&1; then
  echo "ERROR: 'envsubst' not found. Install gettext (e.g. 'sudo apt-get install -y gettext')." >&2
  exit 1
fi

# Restrict substitution to exactly our tokens, so any stray '$' in a manifest
# (there are none today, but be safe) is left untouched.
TOKENS='${CLICKSTREAM_PROJECT_ID} ${PORTAL_PROJECT_ID} ${BUILD_PROJECT_ID} ${REGION}'

echo "Substituting project-ID / region tokens in place..."
echo "  CLICKSTREAM_PROJECT_ID = ${CLICKSTREAM_PROJECT_ID}"
echo "  PORTAL_PROJECT_ID      = ${PORTAL_PROJECT_ID}"
echo "  BUILD_PROJECT_ID       = ${BUILD_PROJECT_ID}"
echo "  REGION                 = ${REGION}"

# Rewrite only the files that actually carry tokens (IAM, buckets, and the day-2
# storage update), in place. grep -l finds them. We iterate newline-delimited
# (our paths never contain newlines), which works under both GNU and BSD grep —
# BSD grep's -Z does not NUL-separate the -l file list, so a -d '' read loop
# would silently process nothing.
count=0
while IFS= read -r f; do
  [ -n "$f" ] || continue
  envsubst "$TOKENS" < "$f" > "$f.tmp" && mv "$f.tmp" "$f"
  echo "  rewrote $f"
  count=$((count + 1))
done < <(grep -rl '\${' templates/ day2/)

echo "Done. Rewrote $count file(s). Tokens are now consumed; you can run kubectl apply."
