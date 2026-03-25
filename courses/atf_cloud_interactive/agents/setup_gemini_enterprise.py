"""Set up a Gemini Enterprise application with an Agent Engine agent.

Operations:
  1. Delete any existing Gemini Enterprise engines (global location)
  2. Create a new engine ("Cymbal Meet - Gemini Enterprise")
  3. Configure identity provider to Google Identity (GSUITE)
  4. Add the deployed Agent Engine agent
  5. Grant all users the agent user role

Usage:
  python setup_gemini_enterprise.py <PROJECT_ID> <PROJECT_NUMBER> <REASONING_ENGINE_NAME>

  REASONING_ENGINE_NAME is the full resource name, e.g.:
    projects/PROJECT_ID/locations/us-central1/reasoningEngines/1234567890
"""

import sys
import time

import google.auth
import google.auth.transport.requests
import requests

LOCATION = "global"
ENGINE_ID = "cymbal-meet-gemini-enterprise"
ENGINE_DISPLAY_NAME = "Cymbal Meet - Gemini Enterprise"
AGENT_DISPLAY_NAME = "Improve Engagement Agent"


def get_auth_headers(project_id):
    credentials, _ = google.auth.default()
    credentials.refresh(google.auth.transport.requests.Request())
    return {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json",
        "X-Goog-User-Project": project_id,
    }


def base_url():
    return f"https://{LOCATION}-discoveryengine.googleapis.com/v1alpha"


def parent(project_id):
    return f"projects/{project_id}/locations/{LOCATION}/collections/default_collection"



# ---- Step 1: Delete existing engines ----------------------------------------

def delete_existing_engines(project_id):
    print("Step 7: Deleting existing Gemini Enterprise engines ...")
    url = f"{base_url()}/{parent(project_id)}/engines"
    resp = requests.get(url, headers=get_auth_headers(project_id))
    resp.raise_for_status()
    engines = resp.json().get("engines", [])

    if not engines:
        print("    No existing engines found.")
        return

    for engine in engines:
        name = engine["name"]
        display = engine.get("displayName", name)
        print(f"    Deleting {display} ({name}) ...")
        del_resp = requests.delete(
            f"{base_url()}/{name}", headers=get_auth_headers(project_id)
        )
        if del_resp.ok:
            print(f"    Delete initiated for {display}.")
        else:
            print(f"    WARNING: Delete returned {del_resp.status_code}: {del_resp.text}")

    print("    Waiting for deletes to complete ...")
    time.sleep(30)
    print("    Done.")


# ---- Step 2: Create engine --------------------------------------------------

def create_engine(project_id, project_number):
    print()
    print("Step 8: Creating Gemini Enterprise application ...")
    url = f"{base_url()}/{parent(project_id)}/engines?engineId={ENGINE_ID}"
    body = {
        "displayName": ENGINE_DISPLAY_NAME,
        "solutionType": "SOLUTION_TYPE_SEARCH",
        "industryVertical": "GENERIC",
        "appType": "APP_TYPE_INTRANET",
        "searchEngineConfig": {
            "searchTier": "SEARCH_TIER_ENTERPRISE",
            "searchAddOns": ["SEARCH_ADD_ON_LLM"],
        },
    }
    resp = requests.post(url, json=body, headers=get_auth_headers(project_id))
    if not resp.ok:
        raise RuntimeError(f"Create engine failed: {resp.status_code} {resp.text}")

    # Engine name uses project number, not project ID
    engine_name = f"projects/{project_number}/locations/{LOCATION}/collections/default_collection/engines/{ENGINE_ID}"
    print(f"    Create initiated. Waiting for engine to be ready ...")
    time.sleep(30)
    print(f"    Engine: {engine_name}")
    return engine_name


# ---- Step 3: Configure identity provider ------------------------------------

def configure_identity_provider(project_id):
    print()
    print("Step 9: Configuring identity provider to Google Identity ...")
    acl_name = f"projects/{project_id}/locations/{LOCATION}/aclConfig"
    url = f"{base_url()}/{acl_name}"
    body = {
        "name": acl_name,
        "idpConfig": {
            "idpType": "GSUITE",
        },
    }
    resp = requests.patch(url, json=body, headers=get_auth_headers(project_id))
    if not resp.ok:
        raise RuntimeError(
            f"Configure identity provider failed: {resp.status_code} {resp.text}"
        )
    print("    Done.")


# ---- Step 4: Add agent ------------------------------------------------------

def add_agent(project_id, engine_name, reasoning_engine_name):
    print()
    print("Step 10: Adding agent to Gemini Enterprise application ...")
    url = (
        f"{base_url()}/{engine_name}"
        f"/assistants/default_assistant/agents"
    )
    body = {
        "displayName": AGENT_DISPLAY_NAME,
        "description": "Cymbal Meet customer engagement orchestrator",
        "adkAgentDefinition": {
            "provisionedReasoningEngine": {
                "reasoningEngine": reasoning_engine_name,
            },
        },
        "sharingConfig": {
            "scope": "ALL_USERS",
        },
    }
    resp = requests.post(url, json=body, headers=get_auth_headers(project_id))
    if not resp.ok:
        raise RuntimeError(f"Add agent failed: {resp.status_code} {resp.text}")
    agent = resp.json()
    print(f"    Agent added: {agent.get('name')}")
    return agent


# ---- Step 5: Configure user permissions --------------------------------------

def configure_permissions(project_id, engine_name):
    print()
    print("Step 11: Configuring user permissions (allUsers) ...")

    # Get current policy to obtain the required etag
    get_url = f"{base_url()}/{engine_name}:getIamPolicy"
    get_resp = requests.post(get_url, json={}, headers=get_auth_headers(project_id))
    if not get_resp.ok:
        raise RuntimeError(
            f"Get IAM policy failed: {get_resp.status_code} {get_resp.text}"
        )
    current_policy = get_resp.json()
    etag = current_policy.get("etag", "")

    # Set updated policy with the etag
    set_url = f"{base_url()}/{engine_name}:setIamPolicy"
    body = {
        "policy": {
            "etag": etag,
            "bindings": [
                {
                    "role": "roles/discoveryengine.user",
                    "members": ["allUsers"],
                },
            ],
        },
    }
    resp = requests.post(set_url, json=body, headers=get_auth_headers(project_id))
    if not resp.ok:
        raise RuntimeError(
            f"Set IAM policy failed: {resp.status_code} {resp.text}"
        )
    print("    Done.")


# ---- Main --------------------------------------------------------------------

def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)

    project_id = sys.argv[1]
    project_number = sys.argv[2]
    reasoning_engine_name = sys.argv[3]

    print()
    print(f"  Reasoning Engine: {reasoning_engine_name}")
    print()

    delete_existing_engines(project_id)
    engine_name = create_engine(project_id, project_number)
    configure_identity_provider(project_id)
    add_agent(project_id, engine_name, reasoning_engine_name)
    configure_permissions(project_id, engine_name)

    print()
    print("Gemini Enterprise setup complete!")


if __name__ == "__main__":
    main()
