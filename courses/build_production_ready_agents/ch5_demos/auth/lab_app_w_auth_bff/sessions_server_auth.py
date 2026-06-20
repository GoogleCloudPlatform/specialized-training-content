"""
ADK Agent API Server - STREAMING VERSION WITH BACKEND-FOR-FRONTEND (BFF) AUTH

A FastAPI server exposing ADK agent functionality via HTTP endpoints with streaming
responses, secured with Google OAuth 2.0 using the **Backend-for-Frontend (BFF)** pattern.

Unlike the Bearer-token variant (../lab_app_w_auth), the browser never holds an OAuth
token. Instead:

  1. The browser hits GET /login; the server runs the OAuth 2.0 Authorization Code flow.
  2. Google redirects back to GET /auth/callback with a one-time code.
  3. The server exchanges the code (using its client secret) for access + refresh tokens
     and stores them SERVER-SIDE, keyed by an opaque session id.
  4. The server sets an HttpOnly, SameSite session cookie. JavaScript cannot read it.
  5. Every API call carries the cookie automatically. The middleware validates the
     session and, when the Google access token is near expiry, refreshes it server-side
     using the stored refresh token -- transparently, with no client involvement.

Because the client never holds the token, there is no client-side token lifetime to
manage: no Bearer headers, no refresh timers, no 401-then-relogin dance.
"""

import json
import logging
import os
import secrets
import sys
import time
from typing import Optional
from urllib.parse import urlencode

import httpx
from agent_sessions import root_agent
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (HTMLResponse, JSONResponse, RedirectResponse,
                               StreamingResponse)
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.examples import VertexAiExampleStore
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from utilities import configure_logging, create_event_summary

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
SESSION_SERVICE_PROVIDER = os.getenv("SESSION_SERVICE_PROVIDER", "in_memory")
EXAMPLE_STORE_NAME = os.getenv("EXAMPLE_STORE_NAME", "")

# OAuth (BFF) configuration
CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
# Where Google redirects after consent; must be registered as an authorized redirect URI.
OAUTH_REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "http://localhost:8080/auth/callback")
# Where to send the browser after a successful login. The client UI is now served
# by THIS server at "/", so the post-login redirect points back to our own root.
CLIENT_APP_URL = os.getenv("CLIENT_APP_URL", "http://localhost:8080/")
# Path to the client HTML served at GET / (same directory as this file).
CLIENT_HTML_PATH = os.path.join(os.path.dirname(__file__), "client_auth.html")
# Cookie name for the BFF session id.
SESSION_COOKIE = "bff_session"
# Refresh the Google access token when it is within this many seconds of expiring.
TOKEN_REFRESH_SKEW_SECONDS = 120

GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v3/userinfo"
OAUTH_SCOPES = "openid email profile"

# ============================================================================
# BFF Session Store (server-side)
# ============================================================================
# Maps an opaque cookie session id -> the user's identity and Google tokens.
# In production this belongs in a shared store (e.g. Redis) so it survives
# restarts and works across multiple server instances. In-memory is fine for
# the demo.
#
#   session_store[sid] = {
#       "email": str,
#       "access_token": str,
#       "refresh_token": str,
#       "expires_at": float (epoch seconds),
#   }
session_store: dict[str, dict] = {}
# Maps a short-lived OAuth "state" value -> issue time, to defend against CSRF
# on the callback. Consumed once on a successful callback. Abandoned logins (the
# user never returns from Google) leak their entry; not reaped in the demo. In
# production these would carry a TTL (e.g. in Redis) so stale entries self-expire.
oauth_states: dict[str, float] = {}


# ============================================================================
# ADK Session Setup
# ============================================================================

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

runner = Runner(
    app_name=APP_NAME,
    agent=root_agent,
    session_service=session_service
)


# ============================================================================
# FastAPI Setup
# ============================================================================

app = FastAPI(title="ADK Agent Server - Streaming with BFF Auth", version="1.0.0")

# CORS: with cookie auth the browser sends credentials, so we CANNOT use "*" for
# the origin -- credentialed requests require an explicit origin and
# allow_credentials=True. Set this to the client app's origin.
CLIENT_ORIGIN = os.getenv("CLIENT_ORIGIN", "http://localhost:8080")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[CLIENT_ORIGIN],   # explicit origin (no "*") because credentials are sent
    allow_credentials=True,          # allow the session cookie to be sent
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# OAuth / Token Helpers
# ============================================================================

async def exchange_code_for_tokens(code: str) -> dict:
    """Exchange a one-time authorization code for Google tokens (server-side)."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GOOGLE_TOKEN_ENDPOINT,
            data={
                "code": code,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri": OAUTH_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        return resp.json()


async def refresh_access_token(refresh_token: str) -> dict:
    """Use a stored refresh token to obtain a fresh access token (server-side)."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            GOOGLE_TOKEN_ENDPOINT,
            data={
                "refresh_token": refresh_token,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "refresh_token",
            },
        )
        resp.raise_for_status()
        return resp.json()


async def fetch_userinfo(access_token: str) -> dict:
    """Fetch the user's profile (email, etc.) using an access token."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            GOOGLE_USERINFO_ENDPOINT,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        resp.raise_for_status()
        return resp.json()


async def get_valid_session(request: Request) -> Optional[dict]:
    """
    Resolve the BFF session from the request cookie and ensure its Google access
    token is still valid, refreshing it SERVER-SIDE when near expiry.

    Returns the session dict (with a fresh token) or None if there is no valid session.
    """
    sid = request.cookies.get(SESSION_COOKIE)
    if not sid or sid not in session_store:
        return None

    sess = session_store[sid]

    # Refresh the Google access token if it is expired or about to expire.
    if time.time() >= sess["expires_at"] - TOKEN_REFRESH_SKEW_SECONDS:
        refresh_token = sess.get("refresh_token")
        if not refresh_token:
            # No refresh token (e.g. Google didn't return one); session is dead.
            logger.info("Session has no refresh token; cannot refresh.")
            session_store.pop(sid, None)
            return None
        try:
            logger.info(f"Refreshing access token for {sess['email']} (server-side)")
            new_tokens = await refresh_access_token(refresh_token)
            sess["access_token"] = new_tokens["access_token"]
            sess["expires_at"] = time.time() + new_tokens.get("expires_in", 3600)
            # Google may or may not return a new refresh token; keep the old one if not.
            if new_tokens.get("refresh_token"):
                sess["refresh_token"] = new_tokens["refresh_token"]
        except Exception as e:
            logger.warning(f"Token refresh failed: {e}")
            session_store.pop(sid, None)
            return None

    return sess


# ============================================================================
# Authentication Middleware (session-cookie based)
# ============================================================================

# Paths that do not require an authenticated session.
PUBLIC_PATHS = {"/", "/login", "/auth/callback"}


@app.middleware("http")
async def authentication_middleware(request: Request, call_next):
    """
    Validate the BFF session cookie on protected routes. On success, store the
    user's identity in request.state for route handlers. The middleware also
    refreshes the Google access token server-side when needed.
    """
    # Allow CORS preflight through.
    if request.method == "OPTIONS":
        return await call_next(request)

    # Public routes (home, OAuth entry/callback) skip auth.
    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    sess = await get_valid_session(request)
    if not sess:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Unauthorized. Please login with Google."},
        )

    # Expose identity to route handlers (mirrors the Bearer variant's user_info).
    request.state.user_info = {"email": sess["email"]}
    return await call_next(request)


# ============================================================================
# OAuth Routes (the BFF)
# ============================================================================

@app.get("/login")
async def login():
    """Begin the OAuth 2.0 Authorization Code flow by redirecting to Google."""
    state = secrets.token_urlsafe(24)
    oauth_states[state] = time.time()
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": OAUTH_SCOPES,
        "state": state,
        # access_type=offline + prompt=consent ensures Google returns a refresh token.
        "access_type": "offline",
        "prompt": "consent",
    }
    return RedirectResponse(f"{GOOGLE_AUTH_ENDPOINT}?{urlencode(params)}")


@app.get("/auth/callback")
async def auth_callback(request: Request):
    """
    Google redirects here with a one-time code. Exchange it for tokens (server-side),
    create a BFF session, set the HttpOnly cookie, and send the user to the client app.
    """
    code = request.query_params.get("code")
    state = request.query_params.get("state")

    # CSRF protection: the state must match one we issued.
    if not state or state not in oauth_states:
        raise HTTPException(status_code=400, detail="Invalid or missing OAuth state.")
    oauth_states.pop(state, None)

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code.")

    try:
        tokens = await exchange_code_for_tokens(code)
        userinfo = await fetch_userinfo(tokens["access_token"])
    except Exception as e:
        logger.error(f"OAuth exchange failed: {e}", exc_info=True)
        raise HTTPException(status_code=502, detail="OAuth exchange failed.")

    sid = secrets.token_urlsafe(32)
    session_store[sid] = {
        "email": userinfo.get("email"),
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token"),
        "expires_at": time.time() + tokens.get("expires_in", 3600),
    }
    logger.info(f"Created BFF session for {userinfo.get('email')}")

    # Redirect to the client app and set the session cookie.
    response = RedirectResponse(CLIENT_APP_URL)
    response.set_cookie(
        key=SESSION_COOKIE,
        value=sid,
        httponly=True,      # JavaScript cannot read this cookie (XSS-resistant)
        secure=False,       # set True in production (HTTPS only)
        samesite="lax",     # sent on top-level navigations back from Google
        max_age=60 * 60 * 24 * 7,
        path="/",
    )
    return response


@app.post("/logout")
async def logout(request: Request):
    """Destroy the server-side session and clear the cookie."""
    sid = request.cookies.get(SESSION_COOKIE)
    if sid:
        session_store.pop(sid, None)
    response = JSONResponse({"status": "logged_out"})
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


@app.get("/me")
async def me(request: Request):
    """Return the authenticated user's identity (used by the client to render state)."""
    # Auth already enforced by middleware, which sets request.state.user_info.
    user_info = getattr(request.state, "user_info", None) or {}
    return {"email": user_info.get("email")}


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

def build_session_summary(session):
    """Return a summary dict for the session (shared by the card and the final response)."""
    return {
        "session_id": session.id,
        "app_name": session.app_name,
        "user_id": session.user_id,
        "state": session.state,
        "events_count": len(session.events),
        "last_update_time": int(session.last_update_time * 1000) if session.last_update_time else None
    }

def build_session_card_data(session):
    """Return a session card data dict for SSE."""
    return {
        "type": "session_card",
        "session": build_session_summary(session),
        "events": summarize_session_events(session)
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
async def home():
    """
    Serve the client UI itself (no authentication required).

    The page is public so the user can reach the "Sign in with Google" button; the
    API routes it calls (/sessions, /chat, /examples, /me) remain protected by the
    cookie middleware. Serving the UI from this same origin means the page and the
    API share an origin, so the session cookie is sent without any CORS gymnastics.
    """
    with open(CLIENT_HTML_PATH, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

if __name__ == "__main__":
    import uvicorn

    # Run the FastAPI application using Uvicorn
    uvicorn.run(
        "sessions_server_auth:app",  # Import string format for reload to work
        host="0.0.0.0",
        port=8080,  # Serves both the client UI ("/") and the protected API
        reload=True
    )
