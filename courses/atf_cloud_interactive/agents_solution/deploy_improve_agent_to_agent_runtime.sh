#!/bin/bash

adk deploy agent_engine \
    --project=$GOOGLE_CLOUD_PROJECT \
    --region=$GOOGLE_CLOUD_LOCATION \
    --env_file=./improve_engagement_agent/.env.deploy \
    --display_name="Improve Engagement Agent" \
    ./improve_engagement_agent

# to update an existing deployment, add:
#     --agent_engine_id=projects/<YOUR_PROJECT_NUMBER>/locations/us-central1/reasoningEngines/<YOUR_ENGINE_ID> \
