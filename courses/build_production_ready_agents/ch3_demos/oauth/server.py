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
import re
import warnings
from typing import Any, AsyncIterator, Optional

# Quiet ADK's [EXPERIMENTAL] UserWarnings and the ADC quota-project warning.
# ADK emits these via a feature decorator, so filter on the message text rather
# than the module path. They are harmless for this demo.
warnings.filterwarnings("ignore", message=r".*\[EXPERIMENTAL\].*", category=UserWarning)
warnings.filterwarnings("ignore", message=r".*end user credentials from Google Cloud SDK.*", category=UserWarning)

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from google.adk.agents.llm_agent import LlmAgent
from google.adk.auth.auth_tool import AuthConfig
from google.adk.auth.credential_service.in_memory_credential_service import \
    InMemoryCredentialService
from google.adk.events import Event
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

load_dotenv()

# Set DEBUG=1 in the environment (or .env) to see the verbose [DEBUG] trace.
DEBUG = os.getenv("DEBUG", "").lower() in ("1", "true", "yes")


def debug(msg: str) -> None:
    if DEBUG:
        print(msg)

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
OAUTH_CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID')
OAUTH_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET')
OAUTH_REDIRECT_URI = os.getenv('OAUTH_REDIRECT_URI', 'http://localhost:8000/oauth-callback.html')

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
            client_secret=OAUTH_CLIENT_SECRET,
            # Setting redirect_uri here means ADK includes it in the auth_uri
            # it generates, so the client doesn't have to build the URL itself.
            redirect_uri=OAUTH_REDIRECT_URI
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
    model='gemini-3.5-flash',
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

# A credential service is what makes OAuth a ONE-TIME event per session.
#
# The BigQuery toolset is a remote, OAuth-protected MCP server. To create the
# toolset, ADK must connect to that server and list its tools, and that
# connection requires OAuth. This happens at the start of the FIRST agent turn
# (before the LLM decides anything), which is why auth appears in response to
# the very first message - this is expected for a connect-time protected toolset.
#
# Without a credential_service, ADK has nowhere to store the token it exchanges,
# so it would re-prompt on every turn. Registering InMemoryCredentialService lets
# ADK cache the exchanged credential and reuse it for the rest of the session.
credential_service = InMemoryCredentialService()

runner = Runner(
    app_name="bigquery_agent",
    agent=root_agent,
    session_service=session_service,
    credential_service=credential_service,
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


# Server-side store for pending OAuth handshakes keyed by
# (user_id, session_id, function_call_id) -> AuthConfig.
# Keeps OAuth client_secret strictly on the server so it is never serialized
# to the browser over SSE (b/585276167).
pending_auth_configs: dict[tuple[str, str, str], AuthConfig] = {}

# Maps session_id -> owner user_id to prevent cross-user session hijacking.
session_owners: dict[str, str] = {}

_USER_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.\-@]{1,64}$")


def redact_auth_config(auth_config: AuthConfig) -> AuthConfig:
    """Return a deep copy of AuthConfig with confidential OAuth secrets removed."""
    redacted = auth_config.model_copy(deep=True)
    for cred in (redacted.raw_auth_credential, redacted.exchanged_auth_credential):
        if cred and getattr(cred, "oauth2", None):
            cred.oauth2.client_secret = None
            if hasattr(cred.oauth2, "code_verifier"):
                cred.oauth2.code_verifier = None
    return redacted


def _extract_auth_response_uri(raw_response: Any) -> Optional[str]:
    """Extract the OAuth callback URL from either a minimal or legacy FunctionResponse dict."""
    if not isinstance(raw_response, dict):
        return None
    direct_uri = raw_response.get("auth_response_uri") or raw_response.get("authResponseUri")
    if isinstance(direct_uri, str) and direct_uri.strip():
        return direct_uri.strip()
    exchanged = (
        raw_response.get("exchanged_auth_credential")
        or raw_response.get("exchangedAuthCredential")
    )
    if isinstance(exchanged, dict):
        oauth2 = exchanged.get("oauth2")
        if isinstance(oauth2, dict):
            nested_uri = oauth2.get("auth_response_uri") or oauth2.get("authResponseUri")
            if isinstance(nested_uri, str) and nested_uri.strip():
                return nested_uri.strip()
    return None


def _find_session_auth_config(session: Any, function_call_id: str) -> Optional[AuthConfig]:
    """Fallback lookup of the requested AuthConfig from session events."""
    for ev in reversed(getattr(session, "events", None) or []):
        try:
            if is_auth_request_event(ev) and get_function_call_id(ev) == function_call_id:
                return get_auth_config(ev)
        except Exception:
            continue
    return None


def build_hydrated_auth_response_message(
    message: dict,
    user_id: str,
    session_id: str,
    session: Any = None,
) -> dict:
    """Re-attach the server-side AuthConfig (including client_secret) to a client FunctionResponse."""
    part = message["parts"][0]["function_response"]
    function_call_id = part.get("id")
    if not function_call_id or not isinstance(function_call_id, str):
        raise ValueError("Missing function_response.id in auth response")

    auth_response_uri = _extract_auth_response_uri(part.get("response"))
    if not auth_response_uri:
        raise ValueError("Missing auth_response_uri in auth response")

    server_auth_config = pending_auth_configs.pop(
        (user_id, session_id, function_call_id), None
    )
    if server_auth_config is None:
        server_auth_config = _find_session_auth_config(session, function_call_id)
    if server_auth_config is None:
        raise ValueError(
            f"No pending auth request found for function_call_id '{function_call_id}'"
        )

    hydrated = server_auth_config.model_copy(deep=True)
    if hydrated.raw_auth_credential and getattr(hydrated.raw_auth_credential, "oauth2", None):
        if OAUTH_CLIENT_SECRET:
            hydrated.raw_auth_credential.oauth2.client_secret = OAUTH_CLIENT_SECRET
    if hydrated.exchanged_auth_credential and getattr(
        hydrated.exchanged_auth_credential, "oauth2", None
    ):
        if OAUTH_CLIENT_SECRET:
            hydrated.exchanged_auth_credential.oauth2.client_secret = OAUTH_CLIENT_SECRET
        hydrated.exchanged_auth_credential.oauth2.auth_response_uri = auth_response_uri

    return {
        "role": "user",
        "parts": [
            {
                "function_response": {
                    "id": function_call_id,
                    "name": "adk_request_credential",
                    "response": hydrated.model_dump(mode="json"),
                }
            }
        ],
    }


# ============================================================================
# FastAPI Setup
# ============================================================================

app = FastAPI(title="ADK Agent Server - Official Pattern", version="1.0.0")

# Restrict CORS to the configured client origin rather than wildcard "*".
CLIENT_ORIGIN = os.getenv("CLIENT_ORIGIN", "http://localhost:8080")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[CLIENT_ORIGIN],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Optional bearer token for authenticating /chat requests in shared deployments.
# TODO(security): For production multi-user deployments, enforce full user
# authentication (see ch5_demos/auth/lab_app_w_auth_bff for the BFF pattern).
API_AUTH_TOKEN = os.getenv("API_AUTH_TOKEN")

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
@app.get("/auth/callback", response_class=HTMLResponse)
async def serve_oauth_callback():
    """Serve the OAuth callback page (both paths, so the registered
    redirect URI can use either)"""
    callback_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "oauth-callback.html")
    with open(callback_path, "r") as f:
        return f.read()

@app.post("/chat")
async def chat(request: Request):
    """
    Main chat endpoint following ADK official auth pattern.
    
    This endpoint:
    1. Runs the agent with user message
    2. Detects if auth is needed (via adk_request_credential event)
    3. Streams auth request (auth_uri + function_call_id only) to client OR streams response chunks
    4. Client handles OAuth and sends FunctionResponse (with auth_response_uri) back
    5. Server re-hydrates AuthConfig server-side and agent retries with valid credentials
    """
    if API_AUTH_TOKEN:
        auth_header = request.headers.get("Authorization", "") if hasattr(request, "headers") else ""
        if auth_header != f"Bearer {API_AUTH_TOKEN}":
            return JSONResponse(status_code=401, content={"error": "Unauthorized"})

    try:
        body = await request.json()
        user_id = body.get("user_id", "default_user")
        if not isinstance(user_id, str) or not _USER_ID_PATTERN.match(user_id):
            return JSONResponse(status_code=400, content={"error": "Invalid user_id"})
        session_id = body.get("session_id")
        message = body.get("message")
        
        debug(f"\n[DEBUG] Received chat request - user_id: {user_id}, session_id: {session_id}")
        
        # Check if this is an auth response (FunctionResponse message)
        is_auth_response = (
            isinstance(message, dict) 
            and message.get("role") == "user"
            and message.get("parts")
            and len(message["parts"]) > 0
            and "function_response" in message["parts"][0]
        )
        
        debug(f"[DEBUG] is_auth_response: {is_auth_response}")
    except Exception as e:
        debug(f"[DEBUG] Error parsing request: {e}")
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
            session_owners[session_id] = user_id
            debug(f"[DEBUG] Created new session: {session_id}")
        except Exception as e:
            debug(f"[DEBUG] Error creating session: {e}")
            import traceback
            traceback.print_exc()
            return {"error": f"Session creation failed: {str(e)}"}, 500
    else:
        owner = session_owners.get(session_id)
        if owner is not None and owner != user_id:
            return JSONResponse(status_code=403, content={"error": "Session user_id mismatch"})
        try:
            session = await session_service.get_session(
                app_name="bigquery_agent",
                user_id=user_id,
                session_id=session_id
            )
            if not session:
                return {"error": "Session not found"}, 404
            session_owners.setdefault(session_id, user_id)
            debug(f"[DEBUG] Retrieved existing session: {session_id}")
        except Exception as e:
            debug(f"[DEBUG] Error retrieving session: {e}")
            import traceback
            traceback.print_exc()
            return {"error": f"Session retrieval failed: {str(e)}"}, 500
    
    # Prepare message content
    try:
        if is_auth_response:
            # Client is sending back auth response - re-hydrate server-side AuthConfig
            # so OAuth client_secret never needs to travel through the browser.
            hydrated_message = build_hydrated_auth_response_message(
                message=message,
                user_id=user_id,
                session_id=session_id,
                session=session,
            )
            content = types.Content(**hydrated_message)
            debug("[DEBUG] Constructed hydrated auth response Content")
        else:
            # Normal text message
            content = types.Content(
                role="user",
                parts=[types.Part(text=message)]
            )
            debug("[DEBUG] Constructed text message Content")
    except Exception as e:
        debug(f"[DEBUG] Error constructing Content: {e}")
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
            
            # `streamed_text` is the text we've already sent to the client for the
            # CURRENT model response. ADK streams a response as a series of partial
            # events whose text grows cumulatively, followed by a final non-partial
            # event carrying the complete text. We emit only the new delta each time,
            # and reset whenever a final event closes out a response - so a tool turn
            # that produces an intermediate message AND a final answer streams both
            # correctly instead of swallowing or duplicating the second one.
            streamed_text = ""
            has_streamed_content = False

            # Set once an auth request has been seen and relayed to the client.
            # We must NOT `break` out of `runner.run_async(...)` here: abandoning
            # the async generator mid-iteration leaves ADK's MCP session / context
            # scopes open, and their later teardown injects GeneratorExit at the
            # wrong suspension point - which raises cancel-scope / context errors on
            # current ADK. Instead we let the generator run to natural completion and
            # simply stop emitting once auth is pending, so ADK closes its own scopes
            # in the task that opened them.
            auth_pending = False

            debug(f"\n[DEBUG] Starting agent run - is_auth_response: {is_auth_response}")

            # Run the agent
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content
            ):
                debug(f"[DEBUG] Event received - partial: {event.partial}, final: {event.is_final_response()}, has_content: {bool(event.content)}")

                # Once auth is pending the run is logically suspended waiting on the
                # human; drain any remaining events without emitting anything more.
                if auth_pending:
                    continue

                # Check if this is an auth request event
                if is_auth_request_event(event):
                    debug("[DEBUG] Auth request detected")
                    # Extract auth details
                    function_call_id = get_function_call_id(event)
                    auth_config = get_auth_config(event)

                    # Get the authorization URL
                    auth_uri = auth_config.exchanged_auth_credential.oauth2.auth_uri

                    # Keep the full AuthConfig (which contains client_secret) server-side
                    # and send only auth_uri and function_call_id to the client (b/585276167).
                    pending_auth_configs[(user_id, session_id, function_call_id)] = (
                        auth_config.model_copy(deep=True)
                    )

                    # Send auth request to client without serializing AuthConfig secrets
                    auth_request_data = {
                        "type": "auth_required",
                        "function_call_id": function_call_id,
                        "auth_uri": auth_uri,
                    }
                    yield f"data: {json.dumps(auth_request_data)}\n\n"

                    # Don't emit further events - drain the generator to completion
                    # so ADK can tear down its MCP/context scopes cleanly.
                    auth_pending = True
                    continue

                # Extract any text on this event (parts may also be tool calls /
                # tool responses, which carry no text and are skipped).
                event_text = ""
                if event.content and event.content.parts:
                    event_text = "".join(
                        part.text for part in event.content.parts
                        if getattr(part, "text", None)
                    )

                if event_text:
                    # Emit only the portion not already sent for this response.
                    # Partial events carry the cumulative text so far; the final
                    # event repeats the full text, so the delta is naturally "".
                    new_text = event_text[len(streamed_text):]
                    if new_text:
                        debug(f"[DEBUG] Streaming delta: {new_text[:50]}...")
                        yield f"data: {json.dumps({'type': 'response_chunk', 'text': new_text, 'is_final': False})}\n\n"
                        has_streamed_content = True
                    streamed_text = event_text

                # A final (non-partial) response closes out the current message.
                # Reset so a subsequent message in the same turn (e.g. the answer
                # produced after a tool call) streams from scratch.
                if event.is_final_response():
                    streamed_text = ""

            debug(f"[DEBUG] Event loop finished - has_streamed_content: {has_streamed_content}")
            
            # Send completion signal
            if has_streamed_content:
                completion_data = {
                    "type": "response_chunk",
                    "text": "",
                    "is_final": True
                }
                yield f"data: {json.dumps(completion_data)}\n\n"
                
        except Exception as e:
            debug(f"[DEBUG] Error in event_generator: {e}")
            import traceback
            traceback.print_exc()
            error_data = {
                "type": "error",
                "message": "An internal error occurred while processing the request."
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-store",
            "Connection": "keep-alive",
            "X-Content-Type-Options": "nosniff",
        }
    )


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)