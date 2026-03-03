# Notes on data agent using and cloud run (no api_server)

## Requirements

- Virtual environment
- Installed dependencies
  
## Config files

- You need a **.env** file for local running
  - Copy the **.env.example** to a file name `.env`
  - Replace the **project_id** placeholders in **.env**

- You need an **agent_card.json** file with correct path to service
  - Copy the **.agent_card.json.template** to a file name `agent_card.json`
  - Running locally, value should be `http://localhost:8080`
  - Before deploying to Cloud Run, you should change to `https://data-agent-<project_number>-us-centra1-run.app`

## Running locally

- Change directories to **data_agent**
- Run this command
  
    ```bash
    uvicorn agent:a2a_app --host 0.0.0.0 --port 8080
    ```

- This will create a server running on port 8080 hosting just the data agent
- The path to the agent card will be `http://localhost:8080`

## To deploy to Cloud Run

- Change directories **data_agent**
- Edit the **url** in the **agent_card.json** file to be `https://data-agent-<project_number>.us-central1.run.app/`
- Set the required environment variables and run the deploy script

    ```bash
    export GOOGLE_CLOUD_PROJECT="<your-project-id>"
    export GOOGLE_CLOUD_LOCATION="us-central1"
    export AGENT_SA="<your-service-account>"
    export AGENT_SERVICE_NAME="data-agent"

    . ./deploy_to_run.sh
    ```
- Service will require auth
- Agent card can be acquired at `https://data-agent-<project_number>.us-central1.run.app/`

## Testing

See the [test README](../../test/README.md) for instructions on testing with the A2A Inspector.
