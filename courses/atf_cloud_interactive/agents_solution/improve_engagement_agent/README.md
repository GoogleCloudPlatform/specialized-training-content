# Notes on Improve Engagement Agent using Agent Engine

## Setup

### Infra created by setup.sh

- Agent service account with role assignments (should be in place if you've run setup)

### ADC

- Service account key file
- ADC configured to use the service account key file

### Virtual Environment

1. From the **agents** directory (not the **improve_engagement_agent** directory), create a virtual environment:

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

### Other agents deployed

- Data Agent deployed to Cloud Run
- Intervention Agent deployed to Cloud Run

### Config files

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
### Telemetry caveat

There's a bug in the ADK library that causes adk web `--otel_to_clound` to fail when you are running using 
Application Default Credentials and a service account key. To make telemetry work, you need to modify
the **adk/telemetry/google_cloud.py** file to specify a scope when creating credentials. 

You can do that in this project by...

1. Make sure you're in the **agents** directory
2. Make sure you have a virtual environment activated
3. Run this command:

    ```bash
    . ./patch_adk_scopes.sh
    ```

### Running locally with **adk web**

1. Make sure you're in the **agents** directory
2. Make sure you have a virtual environment activated
3. Run this command

    ```bash
    adk web --otel_to_cloud --reload --reload_agents
    ```

- This will start the ADK dev UI, typically on `http://localhost:8000`
- The orchestrator will delegate to A2a agents via their Cloud Run A2A endpoints (configured in `.env`)

## Deploying to Agent Engine

- Change directories to **agents**
- Set the required environment variables and run the deploy script

    ```bash
    unset GOOGLE_APPLICATION_CREDENTIALS
    export GOOGLE_CLOUD_PROJECT="<your-project-id>"
    export GOOGLE_CLOUD_LOCATION="us-central1"

    . ./deploy_improve_agent_to_agent_engine.sh
    ```

    Note: The unset is required because the cymbal-agent service account doesn't have permissions to create new
    Agent Engine engines, but your user account does.

## Testing

See the [Test README](../../test/README.md) for details on testing.
