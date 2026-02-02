"""
Simple ADK Agent API Server - STREAMING VERSION WITH GOOGLE AUTHENTICATION

A FastAPI server exposing ADK agent functionality via HTTP endpoints with streaming responses.
Uses in-memory services for simplicity. Client applications make HTTP requests to interact.
Requires Google OAuth authentication for all endpoints except health check.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Optional

from agent_sessions import root_agent
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.examples import VertexAiExampleStore
from google.adk.runners import InMemoryRunner, Runner
from google.adk.sessions import InMemorySessionService
from google.auth.transport import requests as google_requests
from google.genai import types
from google.oauth2 import id_token
from utilities import (clean_json_response, configure_logging,
                       create_event_summary, generate_home_page_html,
                       get_client_url, log_event, log_session)

load_dotenv()

# ============================================================================
# Configure logging
# ============================================================================

configure_logging()
logger = logging.getLogger(__name__)


# ============================================================================
# Read Configuration
# ============================================================================

APP_NAME = os.getenv("APP_NAME", "adk_agent_app")
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "my-gcp-project")
MODEL_LOCATION = os.getenv("MODEL_LOCATION", "us-central1")
AGENT_ENGINE_LOCATION = os.getenv("AGENT_ENGINE_LOCATION", "us-central1")
SESSION_SERVICE_PROVIDER = os.getenv("SESSION_SERVICE_PROVIDER", "in_memory")
REASONING_ENGINE_APP_NAME = os.getenv("REASONING_ENGINE_APP_NAME", "reasoning_engine_app")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
EXAMPLE_STORE_NAME = os.getenv("EXAMPLE_STORE_NAME", "")

# Google OAuth Client ID - Replace with your actual OAuth Client ID from Google Cloud Console
CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")

# ============================================================================
# ADK Session Setup
# ============================================================================

# Create the session service
if SESSION_SERVICE_PROVIDER == "in_memory":
    session_service = InMemorySessionService()
    logger.info(f"Using SESSION_SERVICE_PROVIDER: {SESSION_SERVICE_PROVIDER}")
elif SESSION_SERVICE_PROVIDER == "vertex":
    # STUDENT TASK: Implement VertexSessionService
    logger.info(f"Using SESSION_SERVICE_PROVIDER: {SESSION_SERVICE_PROVIDER}")
elif SESSION_SERVICE_PROVIDER == "db":
    # STUDENT TASK: Implement DatabaseSessionService
    logger.info(f"Using SESSION_SERVICE_PROVIDER: {SESSION_SERVICE_PROVIDER}")
else:
    logger.error(f"Unsupported SESSION_SERVICE_PROVIDER: {SESSION_SERVICE_PROVIDER}")
    sys.exit(1)

# ============================================================================
# ADK Example Store Setup
# ============================================================================
example_store = VertexAiExampleStore(
    examples_store_name=EXAMPLE_STORE_NAME,
)


# ============================================================================
# ADK Runner Setup
# ============================================================================

# Create the runner
runner = Runner(
    app_name=APP_NAME,
    agent=root_agent,
    session_service=session_service
)


# ============================================================================
# FastAPI Setup
# ============================================================================

app = FastAPI(title="ADK Agent Server - Streaming with Auth", version="1.0.0")

# Add CORS middleware to allow requests from any origin for development/testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers in the request
)


# ============================================================================
# Authentication Functions
# ============================================================================

async def validate_token(authorization: Optional[str]) -> Optional[dict]:
    """
    Validates the Bearer token sent in the Authorization header.
    Returns the user info if valid, None otherwise.
    """
    if not authorization:
        return None

    try:
        # Extract the token from "Bearer <token>"
        token = authorization.split(" ")[1]
        
        # Verify the token with Google
        # This checks the signature, expiration, and audience (CLIENT_ID)
        id_info = id_token.verify_oauth2_token(token, google_requests.Request(), CLIENT_ID)
        return id_info
    except (ValueError, IndexError) as e:
        # Invalid token
        logger.warning(f"Token validation error: {e}")
        return None


@app.middleware("http")
async def authentication_middleware(request: Request, call_next):
    """
    Middleware to validate authentication tokens on all routes.
    Stores user_info in request.state for use in route handlers.
    """
    # Skip authentication for root GET (health check and home page)
    if request.method == "GET" and request.url.path == "/":
        return await call_next(request)
    
    # Skip authentication for OPTIONS requests (CORS preflight)
    if request.method == "OPTIONS":
        return await call_next(request)
    
    # For all other requests, validate the token
    auth_header = request.headers.get('Authorization')
    user_info = await validate_token(auth_header)
    
    if not user_info:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Unauthorized. Please login with Google."}
        )
    
    # Store user info in request state for route handlers
    request.state.user_info = user_info
    
    response = await call_next(request)
    return response


# ============================================================================
# Helper Functions
# ============================================================================


async def get_or_create_session(user_id: str, session_id: str | None = None):
    """Get existing session or create new one. Returns (session, session_id)."""
    if not session_id:
        logger.info(f"No session ID provided, creating new session for user {user_id}")
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            state={}
        )
        session_id = session.id
    else:
        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id
        )
        if not session:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid session_id: '{session_id}' not found for user '{user_id}'. Session may have expired or been deleted."
            )
    return session, session_id

def summarize_session_events(session):
    """Return a list of event summaries for a session."""
    return [create_event_summary(evt, idx) for idx, evt in enumerate(session.events)]

def build_session_card_data(session):
    """Return a session card data dict for SSE."""
    return {
        "type": "session_card",
        "session": {
            "session_id": session.id,
            "app_name": session.app_name,
            "user_id": session.user_id,
            "state": session.state,
            "events_count": len(session.events),
            "last_update_time": int(session.last_update_time * 1000) if session.last_update_time else None
        },
        "events": summarize_session_events(session)
    }

def build_session_summary(session):
    """Return a summary dict for the session (for final response)."""
    return {
        "session_id": session.id,
        "app_name": session.app_name,
        "user_id": session.user_id,
        "state": session.state,
        "events_count": len(session.events),
        "last_update_time": int(session.last_update_time * 1000) if session.last_update_time else None
    }

def yield_error_response(message):
    """Yield an error response event for SSE."""
    error_data = {
        "type": "error",
        "message": message
    }
    yield f"data: {json.dumps(error_data)}\n\n"

# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/examples")
async def list_examples(request: Request):
    """List all examples in the Example Store. Requires authentication."""
    # Authentication verified by middleware, user_info available in request.state
    user_email = request.state.user_info.get('email')
    logger.info(f"User {user_email} requesting examples")
    
    examples = []
    try:
        examples = example_store.get_examples(
            query="quiz me on cloud storage"
        )
    except Exception as e:
        logger.error(f"Error fetching examples: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching examples: {str(e)}")
    
    return {"examples": examples}

@app.post("/sessions")
async def create_session(request_data: dict, request: Request):
    """Create a new session for a user. Requires authentication."""
    # Authentication verified by middleware
    user_email = request.state.user_info.get('email')
    
    # Use the authenticated user's email as the user_id
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_email,
        state=request_data.get("initial_state", {})
    )
    
    logger.info(f"Created session {session.id} for user {user_email}")
    
    # Return full session card data so client can display it immediately
    return {
        "session_id": session.id,
        "user_id": session.user_id,
        "session_card": build_session_card_data(session)
    }


@app.post("/chat")
async def chat(request_data: dict, request: Request):
    """Send a message to the agent and get a streaming response with session updates. Requires authentication."""
    # Authentication verified by middleware
    user_email = request.state.user_info.get('email')
    
    session_id = request_data.get("session_id")
    # Use authenticated user's email as user_id
    user_id = user_email
    session, session_id = await get_or_create_session(user_id, session_id)

    logger.info(f"User {user_email} sending message to session {session_id}")

    # Package the message in the correct ADK format
    user_message = types.Content(
        role="user",
        parts=[types.Part(text=request_data["message"])]
    )

    async def event_generator():
        """Generate SSE events for session cards and streaming response chunks."""
        accumulated_text = ""
        event_index = 0

        try:
            # Send initial session card (turn 0) before agent starts
            initial_session_card = build_session_card_data(session)
            yield f"data: {json.dumps(initial_session_card)}\n\n"

            # Run the agent using run_async - it returns a generator of events
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=user_message,
                run_config=RunConfig(
                    streaming_mode=StreamingMode.SSE
                )
            ):
                fc = event.get_function_calls()
                if fc:
                    for call in fc:
                        print (f"call{call}")
                
                fr = event.get_function_responses()
                if fr:
                    for response in fr:
                        print (f"response{response}")
                        
                event_index += 1

                # Stream text chunks as they become available
                # ADK emits chunks in separate events - each event contains new text
                if event.content and event.content.parts and event.partial:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            # Each event contains the new chunk of text
                            chunk_text = part.text
                            accumulated_text += chunk_text

                            # Send this chunk immediately
                            chunk_data = {
                                "type": "response_chunk",
                                "text": chunk_text,
                                "is_final": False
                            }
                            yield f"data: {json.dumps(chunk_data)}\n\n"

                # Check if this is the final response
                if event.is_final_response():
                    break

            
            # Get final session state
            updated_session = await session_service.get_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id
            )

            # Send final session card update after all events are processed
            final_session_card = build_session_card_data(updated_session)
            yield f"data: {json.dumps(final_session_card)}\n\n"

            # Prepare session summary
            session_summary = build_session_summary(updated_session)

            # If no text was accumulated, send an error
            if not accumulated_text:
                logger.error("Agent pipeline did not produce any text response")
                for error_event in yield_error_response("Agent pipeline did not produce any text response."):
                    yield error_event
                return

            # Send final completion event
            completion_data = {
                "type": "response_chunk",
                "text": "",
                "is_final": True,
                "session": session_summary
            }
            yield f"data: {json.dumps(completion_data)}\n\n"
            
        except Exception as e:
            # Log the error with full traceback
            logger.error(f"Error during agent execution: {str(e)}", exc_info=True)
            
            # Send error event to client
            error_data = {
                "type": "error",
                "message": f"Agent execution failed: {str(e)}"
            }
            yield f"data: {json.dumps(error_data)}\n\n"
            
            # Send completion event to unblock the client
            completion_data = {
                "type": "response_chunk",
                "text": "",
                "is_final": True,
                "error": True
            }
            yield f"data: {json.dumps(completion_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with link to client application. No authentication required."""
    client_url = get_client_url(str(request.base_url))
    # Update the HTML to link to the auth client
    html_content = generate_home_page_html(client_url)
    # Replace client.html with client_auth.html if present in the generated HTML
    html_content = html_content.replace('client.html', 'client_auth.html')
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn

    # Run the FastAPI application using Uvicorn
    uvicorn.run(
        "sessions_server_auth:app",  # Import string format for reload to work
        host="0.0.0.0",
        port=8001,  # Different port from the original server
        reload=True
    )
