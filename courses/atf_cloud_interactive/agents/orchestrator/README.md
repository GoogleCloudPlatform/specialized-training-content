# Notes on orchestrator agent using Agent Engine

## Requirements

- Virtual environment
- Installed dependencies

## Config files

- You need a **.env** file for local running
  - Rename the **.env.example** to `.env`
  - Replace the project id and data agent URL placeholders

- You need a **.env.deploy** file for deploying to Agent Engine
  - Rename the **.env.deploy.example** to `.env.deploy`
  - Replace the project id, staging bucket, and data agent URL placeholders

- You need to configure your .agent_engine_config.json file for deployment
  - Rename the **.agent_engine_config.example.json** to `.agent_engine_config.json`
  - Replace the project id placeholder in the service account

- You need a service account keyfile
  - In the console, create a key for cymbal-agent
  - Download the file into the orchestrator directory and name it `cymbal-agent.json`

## Running locally

- Change directories to orchestrator
- Run this command (replacing the placeholder)

    ```bash
    export GOOGLE_APPLICATION_CREDENTIALS="./cymbal-agent.json"
    adk web
    ```

- This will start the ADK dev UI, typically on `http://localhost:8000`
- The orchestrator will delegate data questions to the Data Agent via its Cloud Run A2A endpoint (configured by `DATA_AGENT_URL` in `.env`)

## To deploy to Agent Engine

- Change directories to orchestrator
- Ensure `.env.deploy` and `.agent_engine_config.json` are configured
- Run this command

    ```bash
    adk deploy agent_engine
    ```

- The deployment will use the staging bucket and service account from your config files
