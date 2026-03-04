# Test Notes

## Ad-hoc test scripts

### Setup

Change directories into `test`

```bash
uv venv && uv pip install -r requirements.txt
export GOOGLE_CLOUD_PROJECT=your-project-id
```

### Scripts

| Script           | Description                                                          |
| ---------------- | -------------------------------------------------------------------- |
| `ae-t1.py`       | Send a test query to a deployed Agent Engine and stream the response |
| `dl.py`          | List Vertex AI Search datastores in the project                      |
| `elist.py`       | List all Agent Engines and dump details to `engines.json`            |
| `edel.py`        | Delete all Agent Engines (use with caution)                          |
| `pull-logs.py`   | Pull recent Cloud Logging entries to a JSON file                     |
| `test_upload.py` | Upload a file to GCS via a signed URL                                |

## A2A Testing with A2A Inspector

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

- Make sure the server environment is running per the README in the agent directory
- In the **Inspector** UI, set the agent URL to `http://localhost:8080`
- Click **Connect**
- Use **Chat** to test that the agent is working and responsive

### Testing a Cloud Run server

- Get an identity token for authentication

    ```bash
    gcloud auth print-identity-token
    ```

- In the **Inspector** UI, set the agent URL to the Cloud Run service URL
- In **Authentication and Headers**, choose **Auth Type** of **Bearer Token**
- Enter the token from above into the **Token** field
- Click **Connect**
- Use **Chat** to test that the agent is working and responsive

| Agent              | Local URL               | Cloud Run URL                                                      |
| ------------------ | ----------------------- | ------------------------------------------------------------------ |
| Data Agent         | `http://localhost:8080` | `https://data-agent-<project_number>.us-central1.run.app/`         |
| Intervention Agent | `http://localhost:8080` | `https://intervention-agent-<project_number>.us-central1.run.app/` |


## MCP Testing with MCP Inspector (specifically the GCS MPC server)

### 1. Start the Cloud Run Proxy

Use `gcloud run services proxy` to forward a local port to the deployed service with authenticated headers attached automatically:

```bash
gcloud run services proxy gcs-mcp-server \
  --region=YOUR_REGION \
  --port=8081
# Proxies https://gcs-mcp-server-xxx.run.app → http://localhost:8081
```

### 2. Connect MCP Inspector

Run [MCP Inspector](https://github.com/modelcontextprotocol/inspector) and point it at the proxied local address:

```bash
npx @modelcontextprotocol/inspector
```

Connect with **Streamable HTTP**:

```
http://localhost:8081/mcp
```

All requests are forwarded to Cloud Run with your local `gcloud` credentials, so you're testing the exact deployed service.

---

## Improve Engagement Agent testing

- For local testing, use adk web (per the README.md file in agent directory) and choose **Improve Engagement Agent** 
- For **Agent Engine testing, go to Vertex AI > Agent Engine > Improve Engagement Agent > Playground** in the console
- Ask questions like
  - tbd
  - tbd