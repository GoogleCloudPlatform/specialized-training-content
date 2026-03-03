#!/bin/bash

adk deploy agent_engine \
    --project=$GOOGLE_CLOUD_PROJECT \
    --region=$GOOGLE_CLOUD_LOCATION \
    --env_file=./data_agent/.env.deploy \
    --display_name="Data Agent" \
    ./data_agent

# to update an existing deployment, add:
#     --agent_engine_id=projects/<YOUR_PROJECT_NUMBER>/locations/us-central1/reasoningEngines/<YOUR_ENGINE_ID> \
