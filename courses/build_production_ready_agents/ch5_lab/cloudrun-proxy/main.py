import asyncio
import json
import os
from typing import Optional

import vertexai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from vertexai import agent_engines

# Initialize FastAPI app
app = FastAPI(title="Vertex AI Agent Proxy")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables from .env file if present
load_dotenv()

# Initialize Vertex AI
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
GOOGLE_CLOUD_LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
GOOGLE_CLOUD_STAGING_BUCKET = os.getenv("GOOGLE_CLOUD_STAGING_BUCKET", "")
AGENT_RESOURCE_NAME = os.getenv("AGENT_RESOURCE_NAME", "")
if not GOOGLE_CLOUD_PROJECT:
    raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is not set.")
if not GOOGLE_CLOUD_STAGING_BUCKET:
    raise ValueError("GOOGLE_CLOUD_STAGING_BUCKET environment variable is not set.")
if not AGENT_RESOURCE_NAME:
    raise ValueError("AGENT_RESOURCE_NAME environment variable is not set.")
                     
vertexai.init(
    project=GOOGLE_CLOUD_PROJECT,
    location=GOOGLE_CLOUD_LOCATION,
    staging_bucket=GOOGLE_CLOUD_STAGING_BUCKET
)

# Get the remote agent
remote_agent = agent_engines.get(resource_name=AGENT_RESOURCE_NAME)


# Request/Response models
class CreateSessionRequest(BaseModel):
    user_id: str


class CreateSessionResponse(BaseModel):
    session_id: str
    user_id: str


class QueryRequest(BaseModel):
    user_id: str
    session_id: str
    message: str


# API Endpoints
@app.post("/api/sessions", response_model=CreateSessionResponse)
async def create_session(request: CreateSessionRequest):
    """Create a new agent session for a user."""
    try:
        session = await remote_agent.async_create_session(user_id=request.user_id)
        return CreateSessionResponse(
            session_id=session["id"],
            user_id=request.user_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")


@app.post("/api/query")
async def query_agent(request: QueryRequest):
    """Send a query to the agent and stream the response."""
    async def event_generator():
        try:
            event_count = 0
            async for event in remote_agent.async_stream_query(
                user_id=request.user_id,
                session_id=request.session_id,
                message=request.message,
            ):
                event_count += 1
                print(f"Event #{event_count} received: {type(event).__name__}")
                
                # Unpack event data
                event_type = type(event).__name__
                
                # Extract relevant data based on event type
                event_data = {"type": event_type}
                
                # Handle dict events
                if isinstance(event, dict):
                    event_data.update(event)
                # Handle object events with attributes
                elif hasattr(event, '__dict__'):
                    # Get all non-private attributes
                    attrs = {k: v for k, v in event.__dict__.items() if not k.startswith('_')}
                    event_data.update(attrs)
                # Extract text content if available
                if hasattr(event, 'text'):
                    event_data['text'] = event.text
                elif hasattr(event, 'content'):
                    event_data['content'] = event.content
                
                yield f"data: {json.dumps(event_data, default=str)}\n\n"

            yield f"data: {json.dumps({'is_final': True})}\n\n"
            print(f"Total events received: {event_count}")
        except Exception as e:
            error_data = {
                "type": "error",
                "message": str(e)
            }
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/api/health")
async def health_check():
    """Health check endpoint for Cloud Run."""
    return {"status": "healthy", "service": "vertex-ai-proxy"}


# Serve the index.html at root
@app.get("/")
async def read_root():
    """Serve the main index.html file."""
    return FileResponse("dist/index.html")


# Mount static files
app.mount("/", StaticFiles(directory="dist", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
