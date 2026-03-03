# Test Scripts

Ad-hoc scripts for testing and inspecting the deployed infrastructure. Not part of the course flow.

## Setup

```bash
uv venv && uv pip install -r requirements.txt
export GOOGLE_CLOUD_PROJECT=your-project-id
```

## Scripts

| Script | Description |
|---|---|
| `ae-t1.py` | Send a test query to a deployed Agent Engine and stream the response |
| `dl.py` | List Vertex AI Search datastores in the project |
| `elist.py` | List all Agent Engines and dump details to `engines.json` |
| `edel.py` | Delete all Agent Engines (use with caution) |
| `pull-logs.py` | Pull recent Cloud Logging entries to a JSON file |
| `test_upload.py` | Upload a file to GCS via a signed URL |

## Reference Queries

`da-queries.md` contains sample natural language queries for testing the data analyst agent against the `cymbal_meet` BigQuery dataset.

## Testing with A2A Inspector

The [A2A Inspector](https://github.com/a2aproject/a2a-inspector) is a web-based tool for inspecting and debugging A2A agents.

### Inspector setup

```bash
git clone https://github.com/a2aproject/a2a-inspector.git
cd a2a-inspector
uv sync
cd frontend && npm install && cd ..
bash scripts/run.sh
```

The Inspector UI will be available at `http://127.0.0.1:5001`.

### Testing a local server

- Start the agent locally (e.g. from the agent directory):

    ```bash
    uvicorn agent:a2a_app --host 0.0.0.0 --port 8080
    ```

- In the Inspector UI, set the agent URL to `http://localhost:8080`
- Send a message to verify the agent responds

### Testing a Cloud Run server

- Get an identity token for authentication

    ```bash
    gcloud auth print-identity-token
    ```

- In the Inspector UI, set the agent URL to the Cloud Run service URL
- Add an `Authorization` header with value `Bearer <token>` (using the token from above)
- Send a message to verify the agent responds

### Agent service URLs

| Agent | Local URL | Cloud Run URL |
|---|---|---|
| Data Agent | `http://localhost:8080` | `https://data-agent-<project_number>.us-central1.run.app/` |
| Intervention Agent | `http://localhost:8080` | `https://intervention-agent-<project_number>.us-central1.run.app/` |
