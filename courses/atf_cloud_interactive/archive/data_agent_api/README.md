# Notes on data agent using adk api_server and cloud run

## Requirements

- Virtual environment
- Instaleld dependencies

## Running locally

- You need a .env file for local running
  - Rename the .env.example to .env
  - Replace the project id placeholder
- You need an .agent_engine_config.json file
- Change directories to the data_agent directory
- Run this command
  
    ```bash
    uvicorn agent:a2a_app --host 0.0.0.0 --port 8080
    ```
- This will create an api server running on port 8000 that serves only this agent
- a2a agents are those that have an `agent.json` card file in the root of the subdirectory
- The path to the agent card will be `http://localhost:8000/a2a/data_agent_2/.well-known/agent-card.json`

## To deploy to cloud run

- Edit the url in the agent.json file to be `https://data-agent-906184221373.us-central1.run.app/a2a/data_agent_2/.well-known/agent-card.json`
- Change directories into the data_agent_2 directory
- Run the deploy script `. ./deploy_to_run.sh`
- 