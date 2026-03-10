#!/usr/bin/env bash
set -euo pipefail

# Patches google.adk.telemetry.google_cloud to scope credentials after
# google.auth.default(), fixing "no scopes" errors with ADC + service accounts.

if [[ -z "${VIRTUAL_ENV:-}" ]]; then
  echo "ERROR: No virtual environment is active. Activate one first." >&2
  exit 1
fi

TARGET=$(find "$VIRTUAL_ENV" -path '*/google/adk/telemetry/google_cloud.py' 2>/dev/null | head -1)

if [[ -z "$TARGET" ]]; then
  echo "ERROR: google_cloud.py not found in $VIRTUAL_ENV — is google-adk installed?" >&2
  exit 1
fi

# Check if already patched
if grep -q 'with_scopes' "$TARGET"; then
  echo "Already patched: $TARGET"
  exit 0
fi

# Verify the expected code is present
if ! grep -q 'google_auth if google_auth is not None else google.auth.default()' "$TARGET"; then
  echo "ERROR: Expected code pattern not found in $TARGET — ADK version may differ." >&2
  exit 1
fi

# Apply patch: insert scoping lines after the credentials assignment
sed -i.bak '/google_auth if google_auth is not None else google.auth.default()/,/^  )/{
  /^  )/a\
  if hasattr(credentials, '"'"'with_scopes'"'"') and not credentials.scopes:\
    credentials = credentials.with_scopes(\
        ['"'"'https://www.googleapis.com/auth/cloud-platform'"'"']\
    )
}' "$TARGET"

# Verify the patch applied
if grep -q 'with_scopes' "$TARGET"; then
  echo "Patched successfully: $TARGET"
  rm -f "${TARGET}.bak"
else
  echo "ERROR: Patch failed. Restoring backup." >&2
  mv "${TARGET}.bak" "$TARGET"
  exit 1
fi
