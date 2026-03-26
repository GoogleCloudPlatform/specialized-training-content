import os
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google.auth.transport import requests
from google.oauth2 import id_token
from pydantic import BaseModel

load_dotenv()

app = FastAPI(title="Echo Service")

# Enable CORS to allow the frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CLIENT_ID = os.environ["GOOGLE_OAUTH_CLIENT_ID"]


class EchoRequest(BaseModel):
    message: str


class EchoResponse(BaseModel):
    echo: str


class ErrorResponse(BaseModel):
    error: str


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
        id_info = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)
        return id_info
    except (ValueError, IndexError) as e:
        # Invalid token
        print(f"Token validation error: {e}")
        return None


@app.middleware("http")
async def authentication_middleware(request: Request, call_next):
    """
    Middleware to validate authentication tokens on all routes.
    Stores user_info in request.state for use in route handlers.
    """
    # Skip authentication for root GET (health check)
    if request.method == "GET" and request.url.path == "/":
        return await call_next(request)
    
    # For POST requests, validate the token
    if request.method == "POST":
        auth_header = request.headers.get('Authorization')
        user_info = await validate_token(auth_header)
        
        if not user_info:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"error": "Unauthorized. Please login."}
            )
        
        # Store user info in request state for route handlers
        request.state.user_info = user_info
    
    response = await call_next(request)
    return response


@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "Echo Service"}


@app.post("/", response_model=EchoResponse)
async def echo_service(request: Request, echo_request: EchoRequest):
    """
    Echo endpoint that requires authentication.
    Authentication is handled by middleware, so user_info is already validated.
    """
    # Get user info from middleware (already validated)
    user_info = request.state.user_info
    user_email = user_info.get('email')
    
    # Echo Logic
    response_message = f"Received: '{echo_request.message}' from {user_email}"
    
    return EchoResponse(echo=response_message)


if __name__ == "__main__":
    import uvicorn

    # Use port 8000 for local development (client runs on 8080)
    # PORT can be overridden via environment variable
    port = int(os.environ.get('PORT', 8000))
    uvicorn.run(app, host='0.0.0.0', port=port)
