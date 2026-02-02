# FastAPI Cloud Run Echo Service with Middleware Auth

A FastAPI-based echo service demonstrating Google OAuth 2.0 authentication using ID tokens. This implementation uses middleware for centralized authentication, making it easy to protect all API endpoints.

## Table of Contents

- [Key Features](#key-features)
- [Authentication Flow Overview](#authentication-flow-overview)
- [How Authentication Works](#how-authentication-works)
  - [Client-Side Process](#client-side-process)
  - [Server-Side Process](#server-side-process)
- [Architecture Diagrams](#architecture-diagrams)
- [Implementation Details](#implementation-details)
- [Deployment](#deployment)
- [Local Development](#local-development)

## Key Features

- **FastAPI Framework**: Modern, fast Python web framework with async support
- **Middleware Authentication**: Centralized token validation in middleware layer
- **Google OAuth 2.0**: Uses Google Sign-In with ID tokens (JWT)
- **Pydantic Models**: Type-safe request/response handling
- **Automatic API Docs**: OpenAPI/Swagger documentation at `/docs`

## Authentication Flow Overview

This application uses **Google OAuth 2.0 with ID tokens** to authenticate users. The key concept is:

1. User signs in with Google (client-side)
2. Google provides an **ID token** (a JWT - JSON Web Token)
3. Client sends this token with each API request
4. Server validates the token and extracts user information

```mermaid
sequenceDiagram
    participant User
    participant Browser
    participant Google
    participant CloudRun
    
    User->>Browser: Opens application
    Browser->>Google: Loads Google Sign-In button
    User->>Google: Clicks "Sign in with Google"
    Google->>User: Shows consent screen
    User->>Google: Approves access
    Google->>Browser: Returns ID Token (JWT)
    Browser->>Browser: Stores ID token in memory
    User->>Browser: Types message & clicks Send
    Browser->>CloudRun: POST /echo + Bearer token
    CloudRun->>CloudRun: Middleware validates token
    CloudRun->>Google: Verifies token signature
    Google->>CloudRun: Token valid confirmation
    CloudRun->>CloudRun: Extracts user email from token
    CloudRun->>Browser: Returns echo response
    Browser->>User: Displays response
```

## How Authentication Works

### Client-Side Process

The client (browser) handles authentication in several steps:

#### 1. Loading Google Sign-In

```html
<!-- Google's authentication library -->
<script src="https://accounts.google.com/gsi/client" async defer></script>

<!-- Sign-in button configuration -->
<div id="g_id_onload" 
     data-client_id="YOUR_CLIENT_ID"
     data-callback="handleCredentialResponse">
</div>
```

#### 2. Handling the Sign-In Response

When the user signs in, Google calls the `handleCredentialResponse` function with an ID token:

```javascript
function handleCredentialResponse(response) {
    // response.credential is the JWT ID token
    USER_ID_TOKEN = response.credential;
    
    // Decode token to show user info (optional)
    const payload = JSON.parse(atob(response.credential.split('.')[1]));
    console.log("User email:", payload.email);
}
```

**What's in the ID Token?**
The ID token is a JWT containing:
- `email`: User's email address
- `sub`: User's unique Google ID
- `iat`: Token issued at timestamp
- `exp`: Token expiration timestamp
- `aud`: Client ID (ensures token is for your app)

#### 3. Sending Authenticated Requests

Every API request includes the ID token in the Authorization header:

```javascript
const response = await fetch(CLOUD_RUN_URL, {
    method: "POST",
    headers: {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + USER_ID_TOKEN  // ← ID token here
    },
    body: JSON.stringify({ message: "Hello" })
});
```

**Key Points:**
- Token is sent as `Bearer <token>` in the `Authorization` header
- Token is stored in memory (not localStorage to avoid XSS risks)
- Token expires after 1 hour and needs to be refreshed

### Server-Side Process

The FastAPI server validates authentication using middleware:

#### 1. Middleware Intercepts Requests

```python
@app.middleware("http")
async def authentication_middleware(request: Request, call_next):
    # For POST requests, validate the token
    if request.method == "POST":
        auth_header = request.headers.get('Authorization')
        user_info = await validate_token(auth_header)
        
        if not user_info:
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized"}
            )
        
        # Store user info for route handlers
        request.state.user_info = user_info
    
    return await call_next(request)
```

#### 2. Token Validation Process

```python
async def validate_token(authorization: str) -> dict:
    # Extract token from "Bearer <token>"
    token = authorization.split(" ")[1]
    
    # Verify with Google's public keys
    # This checks:
    # - Signature (token wasn't tampered with)
    # - Expiration (token is still valid)
    # - Audience (token is for this CLIENT_ID)
    id_info = id_token.verify_oauth2_token(
        token, 
        requests.Request(), 
        CLIENT_ID
    )
    
    return id_info  # Contains email, sub, etc.
```

#### 3. Route Handlers Access User Info

```python
@app.post("/")
async def echo_service(request: Request, echo_request: EchoRequest):
    # User info is already validated by middleware
    user_info = request.state.user_info
    user_email = user_info.get('email')
    
    return {"echo": f"Received from {user_email}"}
```

## Architecture Diagrams

### Component Architecture

```mermaid
graph TB
    subgraph "Client Browser"
        HTML[HTML Page]
        JS[JavaScript]
        GSI[Google Sign-In Button]
    end
    
    subgraph "Google Services"
        OAuth[Google OAuth 2.0]
        Keys[Public Keys API]
    end
    
    subgraph "Cloud Run FastAPI"
        MW[Authentication Middleware]
        VAL[Token Validator]
        ROUTE[Echo Endpoint]
    end
    
    HTML --> GSI
    GSI --> OAuth
    OAuth --> JS
    JS -->|POST + Bearer Token| MW
    MW --> VAL
    VAL --> Keys
    VAL --> MW
    MW --> ROUTE
    ROUTE -->|Response| JS
```

### Authentication State Flow

```mermaid
stateDiagram-v2
    [*] --> NotAuthenticated: Page Loads
    NotAuthenticated --> SigningIn: User Clicks Sign In
    SigningIn --> Authenticated: Google Returns Token
    Authenticated --> SendingRequest: User Sends Message
    SendingRequest --> Validated: Middleware Validates Token
    Validated --> Authenticated: Success
    SendingRequest --> NotAuthenticated: Token Invalid (401)
    Authenticated --> NotAuthenticated: Token Expires
```

### Request/Response Flow

```mermaid
flowchart LR
    A[Client] -->|1. POST /echo<br/>Authorization: Bearer token| B[CORS Middleware]
    B --> C[Auth Middleware]
    C -->|2. Extract token| D{Token Valid?}
    D -->|No| E[Return 401]
    D -->|Yes| F[Store user_info<br/>in request.state]
    F --> G[Echo Endpoint]
    G -->|3. Access user_info| H[Generate Response]
    H -->|4. JSON Response| A
    E --> A
```

## Implementation Details

### Middleware vs Per-Route Authentication

This implementation uses **middleware** for authentication, which means:

**Advantages:**
- ✅ Centralized authentication logic
- ✅ All endpoints protected automatically
- ✅ No decorator needed on each route
- ✅ User info available via `request.state`

**Alternative Approach (Per-Route):**
```python
# Without middleware, you'd need to do this on every route:
@app.post("/")
async def echo_service(request: Request):
    auth_header = request.headers.get('Authorization')
    user_info = await validate_token(auth_header)
    if not user_info:
        raise HTTPException(401)
    # ... rest of logic
```

### Security Considerations

1. **Token Validation**: Server verifies token signature using Google's public keys
2. **Audience Check**: Ensures token was issued for this specific CLIENT_ID
3. **Expiration Check**: Tokens expire after 1 hour
4. **HTTPS Only**: ID tokens should only be sent over HTTPS in production
5. **CORS Configuration**: Set specific origins in production, not `"*"`

### Differences from Flask Version

- **Middleware Pattern**: Uses FastAPI middleware instead of per-route decorators
- **Type Safety**: Pydantic models ensure type-safe requests/responses
- **Async Support**: Fully async for better performance
- **Auto Documentation**: OpenAPI docs at `/docs` and `/redoc`
- **Modern Framework**: FastAPI is built on Starlette and Pydantic

## Prerequisites

Before running this application, you need to set up Google OAuth 2.0 credentials:

### 1. Create OAuth 2.0 Client ID

1. Go to [Google Cloud Console → APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials)
2. Click **"+ CREATE CREDENTIALS"** → **"OAuth client ID"**
3. If prompted, configure the OAuth consent screen first:
   - Choose **External** (or Internal if using Google Workspace)
   - Fill in application name and support email
   - Add your email to test users if using External
4. For Application type, select **"Web application"**
5. Add **Authorized JavaScript origins**:
   - `http://localhost:8080` (for local development)
   - Your Cloud Run URL (if deploying the client to Cloud Run)
6. Click **"CREATE"**
7. Copy the **Client ID** (format: `xxxxx-xxxxx.apps.googleusercontent.com`)

### 2. Update Configuration

Replace `CLIENT_ID` in both files with your Client ID:

**In `server.py`:**
```python
CLIENT_ID = "YOUR-CLIENT-ID.apps.googleusercontent.com"
```

**In `index.html`:**
```html
<div id="g_id_onload" 
     data-client_id="YOUR-CLIENT-ID.apps.googleusercontent.com"
     ...
</div>
```

## Deployment

Deploy to Cloud Run:

```bash
gcloud run deploy fastapi-echo-service \
  --source . \
  --region us-central1 \
  --allow-unauthenticated
```

**Important:** Use `--allow-unauthenticated` because:
- We're handling authentication at the **application level** (OAuth tokens)
- Cloud Run's IAM authentication is different (service-to-service)
- The client needs to reach the endpoint to send the OAuth token

**After deployment:**
1. Note the service URL from the deployment output (e.g., `https://fastapi-echo-service-xyz.run.app`)
2. Update `API_URL` in `index.html` with your service URL:
   ```javascript
   const API_URL = "https://your-service-name-123456.us-central1.run.app";
   ```

## Local Development

### Setup

```bash
pip install -r requirements.txt
```

### Testing Scenarios

#### Option 1: Full Local Testing (Client + Server)

Test both client and server locally:

**Terminal 1 - Run Server (port 8000):**
```bash
python server.py
# or with auto-reload:
uvicorn server:app --reload --port 8000
```

**Terminal 2 - Run Client (port 8080):**
```bash
python -m http.server 8080
```

Then open http://localhost:8080 in your browser.

**Configuration:** No changes needed - `index.html` is already configured for `http://localhost:8000`

#### Option 2: Test Local Client Against Cloud Run

Test your local client against a deployed server:

1. **Deploy server to Cloud Run** (see Deployment section above)
2. **Update `API_URL` in `index.html`:**
   ```javascript
   const API_URL = "https://your-service-name-123456.us-central1.run.app";
   ```
3. **Run client locally:**
   ```bash
   python -m http.server 8080
   ```
4. Open http://localhost:8080 in your browser

**Note:** Remember to change `API_URL` back to `http://localhost:8000` when switching back to full local testing.

## API Documentation

Once the server is running locally, visit:
- http://localhost:8000/docs - Interactive Swagger UI
- http://localhost:8000/redoc - ReDoc documentation
- http://localhost:8000 - Health check endpoint
