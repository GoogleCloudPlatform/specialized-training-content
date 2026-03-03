# Notes on orchestrator agent using Agent Engine

## Requirements

- Virtual environment
- Installed dependencies

## Config files

- You need a **.env** file for local running
  - Copy the **.env.example** to a file name `.env`
  - Replace the placeholders in **.env**

- You need a **.env.deploy** file for deploying to Agent Engine
  - Copy the **.env.deploy.example** to a file name `.env.deploy`
  - Replace the placeholders in **.env.deploy**

- You need an **.agent_engine_config.json** file for deployment
  - Copy the **.agent_engine_config.json.template** to a file name `.agent_engine_config.json`
  - Replace the project id placeholder in the service account

## Running locally

- Change directories to **agents**
- Run this command

    ```bash
    adk web
    ```

- This will start the ADK dev UI, typically on `http://localhost:8000`
- The orchestrator will delegate data questions to the Data Agent via its Cloud Run A2A endpoint (configured by `DATA_AGENT_URL` in `.env`)

## To deploy to Agent Engine

- Change directories to **agents**
- Set the required environment variables and run the deploy script

    ```bash
    export GOOGLE_CLOUD_PROJECT="<your-project-id>"
    export GOOGLE_CLOUD_LOCATION="us-central1"

    . ./deploy_orch_agent_to_agent_engine.sh
    ```

## Testing
