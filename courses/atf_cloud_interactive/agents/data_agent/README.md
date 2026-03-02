# Notes on data agent using and cloud run (no api_server)

## Requirements

- Virtual environment
- Installed dependencies
  
## Config files

- You need a **.env** file for local running
  - Rename the **.env.example** to `.env`
  - Replace the project id placeholders

- You need to configure your agent_card.json file with correct path to service
  - Running locally, value should be `http://localhost:8080`
  - Before deploying to Cloud Run, you should change to `https://data-agent-<project_number>-us-centra1-run.app`

## Running locally

- Change directories data_agent
- Run this command
  
    ```bash
    uvicorn agent:a2a_app --host 0.0.0.0 --port 8080
    ```

- This will create a server running on port 8080 hosting just the data agent
- The path to the agent card will be `http://localhost:8080`

## To deploy to cloud run

- Change directories data_agent
- Edit the `url` in the agent.json file to be `https://data-agent-<project_number>.us-central1.run.app/`
- Edit the deploy_to_run.sh script, replacing the `project_id` placeholder
- Run the deploy script `. ./deploy_to_run.sh`
- Service will require auth
  - You can get ID token with gcloud auth print-identity-token
  - You can pass in Authorization header with Bearer <token>
- Agent card can be acquired at `https://data-agent-<project_number>.us-central1.run.app/`