"""
ADK Agent Server - Following Official ADK Authentication Pattern

This server implements the event-based OAuth flow as documented in:
https://google.github.io/adk-docs/tools-custom/authentication/

Key differences from custom approach:
1. Agent runs FIRST, detects auth needs during execution
2. Emits 'adk_request_credential' events when auth needed
3. Client handles OAuth and sends FunctionResponse back
4. ADK handles token exchange automatically
"""

import asyncio
import json
import os
from typing import AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from google.adk.agents.llm_agent import LlmAgent
from google.adk.auth.auth_tool import AuthConfig
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

load_dotenv()

# ============================================================================
# Agent Configuration (from the blog article example)
# ============================================================================

from fastapi.openapi.models import (OAuth2, OAuthFlowAuthorizationCode,
                                    OAuthFlows)
from google.adk.auth.auth_credential import (AuthCredential,
                                             AuthCredentialTypes, OAuth2Auth)
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import \
    StreamableHTTPConnectionParams

# OAuth configuration - matches the blog article
OAUTH_CLIENT_ID = os.getenv('OAUTH_CLIENT_ID')
OAUTH_CLIENT_SECRET = os.getenv('OAUTH_CLIENT_SECRET')

def get_oauth2_mcp_tool():
    """Create BigQuery MCP tool with OAuth - ADK will handle the flow"""
    auth_scheme = OAuth2(
        flows=OAuthFlows(
            authorizationCode=OAuthFlowAuthorizationCode(
                authorizationUrl="https://accounts.google.com/o/oauth2/auth",
                tokenUrl="https://oauth2.googleapis.com/token",
                scopes={
                    "https://www.googleapis.com/auth/bigquery": "bigquery"
                },
            )
        )
    )
    
    auth_credential = AuthCredential(
        auth_type=AuthCredentialTypes.OAUTH2,
        oauth2=OAuth2Auth(
            client_id=OAUTH_CLIENT_ID,
            client_secret=OAUTH_CLIENT_SECRET
        ),
    )
    
    bigquery_mcp_tool = McpToolset(
        connection_params=StreamableHTTPConnectionParams(
            url='https://bigquery.googleapis.com/mcp'
        ),
        auth_credential=auth_credential,
        auth_scheme=auth_scheme,
    )
    
    return bigquery_mcp_tool

# Create the agent
root_agent = LlmAgent(
    model='gemini-3-flash-preview',
    name='bigquery_analyst',
    description='Data analyst with BigQuery access',
    instruction='''You are a helpful data analyst with access to BigQuery.
    
When users ask about data:
1. List available datasets if needed
2. Check table schemas
3. Run queries to answer questions
4. Explain results clearly
''',
    tools=[get_oauth2_mcp_tool()],
)

# ============================================================================
# ADK Setup
# ============================================================================

session_service = InMemorySessionService()
runner = Runner(
    app_name="bigquery_agent",
    agent=root_agent,
    session_service=session_service
)

# ============================================================================
# Helper Functions (from ADK docs)
# ============================================================================

def is_auth_request_event(event: Event) -> bool:
    """Check if event is requesting authentication"""
    return bool(
        event.content
        and event.content.parts
        and len(event.content.parts) > 0
        and event.content.parts[0].function_call
        and event.content.parts[0].function_call.name == 'adk_request_credential'
        and event.long_running_tool_ids
        and event.content.parts[0].function_call.id in event.long_running_tool_ids
    )

def get_function_call_id(event: Event) -> str:
    """Extract function call ID from event"""
    if (
        event.content
        and event.content.parts
        and len(event.content.parts) > 0
        and event.content.parts[0].function_call
        and event.content.parts[0].function_call.id
    ):
        return event.content.parts[0].function_call.id
    raise ValueError(f'Cannot get function call id from event {event}')

def get_auth_config(event: Event) -> AuthConfig:
    """Extract AuthConfig from auth request event"""
    if (
        event.content
        and event.content.parts
        and len(event.content.parts) > 0
        and event.content.parts[0].function_call
        and event.content.parts[0].function_call.args
        and event.content.parts[0].function_call.args.get('authConfig')
    ):
        auth_config_dict = event.content.parts[0].function_call.args.get('authConfig')
        if isinstance(auth_config_dict, dict):
            return AuthConfig.model_validate(auth_config_dict)
        elif isinstance(auth_config_dict, AuthConfig):
            return auth_config_dict
    raise ValueError(f'Cannot get auth config from event {event}')

# ============================================================================
# FastAPI Setup
# ============================================================================

app = FastAPI(title="ADK Agent Server - Official Pattern", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Endpoints
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def serve_client():
    """Serve the web client"""
    # We'll return the path to the client file
    # In production, you'd serve this properly
    return """
    <!DOCTYPE html>
    <html>
    <head><title>ADK Agent Client</title></head>
    <body>
        <h1>ADK Agent Client</h1>
        <p>Please use client.html instead - this is just the API server.</p>
        <p>Open client.html in your browser and point it to http://localhost:8000</p>
    </body>
    </html>
    """

@app.get("/oauth-callback.html", response_class=HTMLResponse)
async def serve_oauth_callback():
    """Serve the OAuth callback page"""
    with open("oauth-callback.html", "r") as f:
        return f.read()

@app.post("/chat")
async def chat(request: Request):
    """
    Main chat endpoint following ADK official auth pattern.
    
    This endpoint:
    1. Runs the agent with user message
    2. Detects if auth is needed (via adk_request_credential event)
    3. Streams auth request to client OR streams response chunks
    4. Client handles OAuth and sends FunctionResponse back
    5. Agent retries with valid credentials
    """
    try:
        body = await request.json()
        user_id = body.get("user_id", "default_user")
        session_id = body.get("session_id")
        message = body.get("message")
        
        print(f"\n[DEBUG] Received chat request - user_id: {user_id}, session_id: {session_id}")
        print(f"[DEBUG] Message type: {type(message)}, content: {str(message)[:200]}")
        
        # Check if this is an auth response (FunctionResponse message)
        is_auth_response = (
            isinstance(message, dict) 
            and message.get("role") == "user"
            and message.get("parts")
            and len(message["parts"]) > 0
            and "function_response" in message["parts"][0]
        )
        
        print(f"[DEBUG] is_auth_response: {is_auth_response}")
    except Exception as e:
        print(f"[DEBUG] Error parsing request: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}, 400
    
    # Get or create session
    if not session_id:
        try:
            session = await session_service.create_session(
                app_name="bigquery_agent",
                user_id=user_id,
                state={}
            )
            session_id = session.id
            print(f"[DEBUG] Created new session: {session_id}")
        except Exception as e:
            print(f"[DEBUG] Error creating session: {e}")
            import traceback
            traceback.print_exc()
            return {"error": f"Session creation failed: {str(e)}"}, 500
    else:
        try:
            session = await session_service.get_session(
                app_name="bigquery_agent",
                user_id=user_id,
                session_id=session_id
            )
            if not session:
                return {"error": "Session not found"}, 404
            print(f"[DEBUG] Retrieved existing session: {session_id}")
        except Exception as e:
            print(f"[DEBUG] Error retrieving session: {e}")
            import traceback
            traceback.print_exc()
            return {"error": f"Session retrieval failed: {str(e)}"}, 500
    
    # Prepare message content
    try:
        if is_auth_response:
            # Client is sending back auth response - reconstruct Content
            content = types.Content(**message)
            print(f"[DEBUG] Constructed auth response Content")
        else:
            # Normal text message
            content = types.Content(
                role="user",
                parts=[types.Part(text=message)]
            )
            print(f"[DEBUG] Constructed text message Content")
    except Exception as e:
        print(f"[DEBUG] Error constructing Content: {e}")
        import traceback
        traceback.print_exc()
        return {"error": f"Content construction failed: {str(e)}"}, 400
    
    async def event_generator() -> AsyncIterator[str]:
        """
        Stream events back to client.
        
        Handles both partial streaming chunks and complete final responses.
        """
        try:
            # Notify client of session
            yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
            
            accumulated_text = ""
            has_streamed_content = False
            
            print(f"\n[DEBUG] Starting agent run - is_auth_response: {is_auth_response}")
            if is_auth_response:
                print(f"[DEBUG] Auth response content: {content}")
            
            # Run the agent
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content
            ):
                print(f"[DEBUG] Event received - partial: {event.partial}, has_content: {bool(event.content)}")
                
                # Check if this is an auth request event
                if is_auth_request_event(event):
                    print("[DEBUG] Auth request detected")
                    # Extract auth details
                    function_call_id = get_function_call_id(event)
                    auth_config = get_auth_config(event)
                    
                    # Get the authorization URL
                    auth_uri = auth_config.exchanged_auth_credential.oauth2.auth_uri
                    
                    # Send auth request to client
                    auth_request_data = {
                        "type": "auth_required",
                        "function_call_id": function_call_id,
                        "auth_uri": auth_uri,
                        "auth_config": auth_config.model_dump(mode='json')
                    }
                    yield f"data: {json.dumps(auth_request_data)}\n\n"
                    
                    # Don't process more events - wait for auth response
                    break
                
                # Process content from events (both partial and non-partial)
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            chunk_text = part.text
                            print(f"[DEBUG] Text chunk: {chunk_text[:50]}...")
                            
                            # For partial events, send only new text
                            if event.partial:
                                # Calculate new text by removing accumulated text
                                new_text = chunk_text[len(accumulated_text):]
                                if new_text:
                                    accumulated_text = chunk_text
                                    chunk_data = {
                                        "type": "response_chunk",
                                        "text": new_text,
                                        "is_final": False
                                    }
                                    yield f"data: {json.dumps(chunk_data)}\n\n"
                                    has_streamed_content = True
                            else:
                                # Non-partial event - might be complete response
                                # Send the full text if we haven't streamed anything yet
                                if not has_streamed_content:
                                    chunk_data = {
                                        "type": "response_chunk",
                                        "text": chunk_text,
                                        "is_final": False
                                    }
                                    yield f"data: {json.dumps(chunk_data)}\n\n"
                                    accumulated_text = chunk_text
                                    has_streamed_content = True
            
            print(f"[DEBUG] Event loop finished - has_streamed_content: {has_streamed_content}")
            
            # Send completion signal
            if has_streamed_content:
                completion_data = {
                    "type": "response_chunk",
                    "text": "",
                    "is_final": True
                }
                yield f"data: {json.dumps(completion_data)}\n\n"
                
        except Exception as e:
            print(f"[DEBUG] Error in event_generator: {e}")
            import traceback
            traceback.print_exc()
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


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)