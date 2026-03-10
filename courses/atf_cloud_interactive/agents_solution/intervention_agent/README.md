# Notes on intervention agent using and cloud run (no api_server)

## Setup

### Infra created by setup.sh

- Agent service account with role assignments (should be in place if you've run setup)
- A Vertex AI Search datastore with troubleshooting/engagement content
- A GCS bucket for storing generated intervention PDFs
- A deployed GCS MCP server endpoint

### ADC

- Service account key file
- ADC configured to use the service accoutn key file

### Virtual Environment

1. From the **intervention_agent** directory, create a virtual environment:

    ```bash
    uv venv
    ```

2. Activate the virtual environment:

    ```bash
    source .venv/bin/activate
    ```

3. Install dependencies:

    ```bash
    uv pip install -r requirements.txt
    ```

### Config files

- You need a **.env** file for local running
  - Copy the **.env.example** to a file name `.env`
  - Replace the placeholders in **.env**

- You need an **agent_card.json** file with correct path to service
  - Copy the **agent_card.json.template** to a file name `agent_card.json`
  - Running locally, value should be `http://localhost:8080`
  - Before deploying to Cloud Run, you should change to `https://intervention-agent-<project_number>-us-centra1-run.app`

## Running locally - Linux

- Change directories to **intervention_agent**
- Run the following to start the server:

    ```bash
    uvicorn agent:a2a_app --host 0.0.0.0 --port 8080
    ```

- This will create a server running on port 8080 hosting just the intervention agent
- The path to the agent card will be `http://localhost:8080`

## Running locally - Mac

> [!WARNING]
> I've had all sort of problems with weasyprint on mac
> For that, I suggest testing locally using docker

- Change directories to **intervention_agent**
- Build and run a Docker version of your agent server

```bash
    export GOOGLE_CLOUD_PROJECT="project_id"
    export GOOGLE_CLOUD_LOCATION="us-central1"
    export AGENT_SA="cymbal-agent@project_id.iam.gserviceaccount.com"
    export AGENT_SERVICE_NAME="intervention-agent"
    export VS_DATASTORE_ID="data_store_resource-path"
    export GCS_MCP_ENDPOINT="https://gcs-mcp-server-project_number.us-central1.run.app/mcp"
    export INTERVENTIONS_BUCKET="gs://project_id-cymbal-meet-interventions"
    export SA_KEY="local/path/to/sa_key.json"

    docker build -t intervention-agent .

    docker run -p 8080:8080 \
    -e GOOGLE_CLOUD_PROJECT=jwd-atf-int \
    -e VS_DATASTORE_ID="$VS_DATASTORE_ID" \
    -e GCS_MCP_ENDPOINT="$GCS_MCP_ENDPOINT" \
    -e GOOGLE_APPLICATION_CREDENTIALS=/app/sa-key.json \
    -v $SA_KEY:/app/sa-key.json:ro \
    -d \
    --name intervention\
    intervention-agent
```

## To deploy to Cloud Run

- Change directories **intervention_agent**
- Edit the **url** in the **agent_card.json** file to be `https://intervention-agent-<project_number>.us-central1.run.app/`
  - You can get the number by running this command:

  ```bash
  gcloud projects describe $(gcloud config get-value project) --format="value(projectNumber)"
  ```

- Set the required environment variables and run the deploy script

    ```bash
    export GOOGLE_CLOUD_PROJECT="<your-project-id>"
    export GOOGLE_CLOUD_LOCATION="us-central1"
    export AGENT_SA="<your-service-account>"
    export AGENT_SERVICE_NAME="intervention-agent"
    export VS_DATASTORE_ID="<your-datastore-id>"
    export GCS_MCP_ENDPOINT="<your-gcs-mcp-server-url>/mcp"
    export INTERVENTIONS_BUCKET="gs://<your-project-id>-cymbal-meet-interventions"

    . ./deploy_to_run.sh
    ```
- Service will require auth
- Agent card can be acquired at `https://intervention-agent-<project_number>.us-central1.run.app/`

## Testing

See the [test README](../../test/README.md) for instructions on testing with the A2A Inspector.