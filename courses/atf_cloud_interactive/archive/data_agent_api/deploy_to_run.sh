export GOOGLE_CLOUD_PROJECT="jwd-atf-int"
export GOOGLE_CLOUD_LOCATION="us-central1"
export AGENT_SA="cymbal-agent"
export APP_NAME="data_agent_2"
export GOOGLE_GENAI_USE_VERTEXAI=True
export AGENT_SERVICE_NAME="data-agent-2"


adk deploy cloud_run \
    --project=$GOOGLE_CLOUD_PROJECT \
    --region=$GOOGLE_CLOUD_LOCATION \
    --trace_to_cloud \
    --a2a \
    --service_name=$AGENT_SERVICE_NAME \
    --app_name=$APP_NAME \
    ./agents\
    -- \
    --service-account $AGENT_SA