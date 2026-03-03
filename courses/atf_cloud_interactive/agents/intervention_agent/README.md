# Notes on intervention agent using and cloud run (no api_server)

## Requirements

- Virtual environment
- Installed dependencies
- A Vertex AI Search datastore with troubleshooting/engagement content
- A GCS bucket for storing generated intervention PDFs
- A deployed GCS MCP server endpoint

## Config files

- You need a **.env** file for local running
  - Copy the **.env.example** to a file name `.env`
  - Replace the placeholders in **.env**

- You need an **agent_card.json** file with correct path to service
  - Copy the **agent_card.json.template** to a file name `agent_card.json`
  - Running locally, value should be `http://localhost:8080`
  - Before deploying to Cloud Run, you should change to `https://intervention-agent-<project_number>-us-centra1-run.app`

## Running locally

- Change directories to **intervention_agent**
- WeasyPrint requires native system libraries for PDF generation. On macOS:

    ```bash
    brew install pango
    export DYLD_LIBRARY_PATH=/opt/homebrew/lib
    ```

- Run the following to start the server:

    ```bash
    uvicorn agent:a2a_app --host 0.0.0.0 --port 8080
    ```

- This will create a server running on port 8080 hosting just the intervention agent
- The path to the agent card will be `http://localhost:8080`

## To deploy to Cloud Run

- Change directories **intervention_agent**
- Edit the **url** in the **agent_card.json** file to be `https://intervention-agent-<project_number>.us-central1.run.app/`
- Set the required environment variables and run the deploy script

    ```bash
    export GOOGLE_CLOUD_PROJECT="<your-project-id>"
    export GOOGLE_CLOUD_LOCATION="us-central1"
    export AGENT_SA="<your-service-account>"
    export AGENT_SERVICE_NAME="intervention-agent"
    export VS_DATASTORE_ID="<your-datastore-id>"
    export GCS_MCP_ENDPOINT="<your-gcs-mcp-server-url>"
    export INTERVENTIONS_BUCKET="gs://<your-project-id>-interventions"

    . ./deploy_to_run.sh
    ```
- Service will require auth
- Agent card can be acquired at `https://intervention-agent-<project_number>.us-central1.run.app/`

## Testing

See the [test README](../../test/README.md) for instructions on testing with the A2A Inspector.