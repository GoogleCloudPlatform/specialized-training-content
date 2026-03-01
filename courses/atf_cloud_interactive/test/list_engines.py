"""List all Agent Engines and their configuration details."""

import json

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
    output_file = "engines.json"
    with open(output_file, "w") as f:
        json.dump(engines, f, indent=2)
    print(f"Wrote {len(engines)} engine(s) to {output_file}")
