
export GOOGLE_CLOUD_PROJECT="jwd-atf-int"
export GOOGLE_CLOUD_LOCATION="us-central1" # Example location
export AGENT_PATH="../data_agent" # Assuming capital_agent is in the current directory
export SERVICE_NAME="data-agent-service"
export APP_NAME="data_agent_app"

adk deploy cloud_run \
    --project=$GOOGLE_CLOUD_PROJECT \
    --region=$GOOGLE_CLOUD_LOCATION \
    --service_name=$SERVICE_NAME \
    --app_name=$APP_NAME \
    --with_ui \
    $AGENT_PATH \
    -- \
    --service-account=cymbal-agent@jwd-atf-int.iam.gserviceaccount.com

export APP_URL="https://data-agent-service-906184221373.us-central1.run.app"
export TOKEN=$(gcloud auth print-identity-token)
curl -X GET -H "Authorization: Bearer $TOKEN" $APP_URL/list-apps
curl -X POST -H "Authorization: Bearer $TOKEN" \
    $APP_URL/apps/data_agent_app/users/user_123/sessions/session_abc \
    -H "Content-Type: application/json" \
    -d '{"preferred_language": "English", "visit_count": 5}'
curl -X POST -H "Authorization: Bearer $TOKEN" \
    $APP_URL/run_sse \
    -H "Content-Type: application/json" \
    -d '{
    "app_name": "data_agent_app",
    "user_id": "user_123",
    "session_id": "session_abc",
    "new_message": {
        "role": "user",
        "parts": [{
        "text": "Which customers have fewer than 30% of licensed users logging in?"
        }]
    },
    "streaming": false
    }'