"""Delete all Agent Engines."""

import google.auth
import google.auth.transport.requests
import requests

PROJECT_ID = "jwd-atf-int"
LOCATION = "us-central1"

# Get default credentials
credentials, _ = google.auth.default()
credentials.refresh(google.auth.transport.requests.Request())

base_url = f"https://{LOCATION}-aiplatform.googleapis.com/v1"
parent = f"projects/{PROJECT_ID}/locations/{LOCATION}"
headers = {"Authorization": f"Bearer {credentials.token}"}

# List all reasoning engines
resp = requests.get(f"{base_url}/{parent}/reasoningEngines", headers=headers)
resp.raise_for_status()
data = resp.json()

engines = data.get("reasoningEngines", [])
if not engines:
    print("No agent engines found.")
else:
    EXCLUDE = {}
    to_delete = [e for e in engines if e.get("displayName") not in EXCLUDE]
    print(f"Found {len(engines)} engine(s), deleting {len(to_delete)} (excluding {EXCLUDE})...")
    for engine in to_delete:
        name = engine["name"]
        del_resp = requests.delete(f"{base_url}/{name}", headers=headers, params={"force": "true"})
        if del_resp.ok:
            print(f"  Deleted {name}")
        else:
            print(f"  Failed to delete {name}: {del_resp.status_code} {del_resp.text}")
    print("Done.")
