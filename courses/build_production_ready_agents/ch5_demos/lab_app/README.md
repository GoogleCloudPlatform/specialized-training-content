# ADK Agent Lab Application

A streaming chat application demonstrating Google's Agent Development Kit (ADK) with session management and real-time streaming responses.

## What It Does

This application provides an interactive chat interface for conversing with a Gemini-powered AI agent that specializes in Google Cloud Platform (GCP) services. The agent can:

- Answer questions about GCP concepts and services
- Check service availability across different GCP regions
- Maintain conversation context through session management
- Stream responses in real-time for better user experience

## Architecture

The application consists of three main components:

### 1. **Backend Server** ([sessions_server.py](sessions_server.py))
- **Framework**: FastAPI with async/await support
- **Port**: 8000
- **Features**:
  - RESTful API endpoints for chat interactions
  - Server-Sent Events (SSE) for real-time streaming
  - Session management with configurable storage (in-memory, database, or Vertex AI)
  - Example store integration for few-shot learning
  - CORS enabled for local development

### 2. **ADK Agent** ([agent_sessions.py](agent_sessions.py))
- **Model**: Gemini 3 Flash Preview (configurable via `.env`)
- **Role**: Cloud technology tutor
- **Tools**: 
  - `check_gcp_service_availability` - Custom function to check GCP service regions
  - `google_search` - Web search capability
- **Configuration**: Session-aware with memory and context retention

### 3. **Web Client** ([client.html](client.html))
- **Technology**: Vanilla HTML/CSS/JavaScript
- **Port**: 8080 (served by [client_server.py](client_server.py))
- **Features**:
  - Clean, modern UI with streaming message display
  - Session management controls
  - Markdown rendering for formatted responses
  - Real-time session event tracking

### Supporting Components

- **[utilities.py](utilities.py)**: Helper functions for logging, event handling, and data formatting
- **[client_server.py](client_server.py)**: Simple HTTP server to serve the static HTML client

## Data Flow

```
User → Web Client (port 8080) → API Server (port 8000) → ADK Agent → Gemini API
                                       ↓
                               Session Service (in-memory/DB/Vertex)
                                       ↓
                               Example Store (Vertex AI)
```

## Local Setup

### Prerequisites

- Python 3.12 or higher
- Google Cloud Platform account with billing enabled
- Vertex AI API enabled in your GCP project
- Service account credentials or `gcloud` authentication configured

### 1. Clone and Navigate

```bash
cd courses/build_production_ready_agents/ch5_demos/lab_app
```

### 2. Create Virtual Environment

```bash
python3.12 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file and customize it:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```dotenv
# Application Configuration
APP_NAME="adk_agent_app"                    # Your app name
GOOGLE_CLOUD_PROJECT="your-project-id"      # Required: Your GCP project ID

# GCP Region Settings
AGENT_ENGINE_LOCATION="us-central1"         # Vertex AI region for agents
MODEL_LOCATION="global"                      # Model deployment region

# Session Storage Options
SESSION_SERVICE_PROVIDER="in_memory"        # Options: in_memory, vertex, db
MEMORY_SERVICE_PROVIDER="in_memory"         # Options: in_memory, vertex, db

# Optional: Vertex AI Resources (if using vertex storage)
REASONING_ENGINE_APP_NAME=""                # Full resource name if using Reasoning Engine
EXAMPLE_STORE_NAME=""                       # Example store resource name (format: projects/PROJECT_ID/locations/LOCATION/exampleStores/STORE_ID)

# Optional: Database Configuration (if using db storage)
DATABASE_URL=postgresql+asyncpg://adk:This_is_the_adk_password!@localhost:5432/adk_sessions

# Model Configuration
GOOGLE_GENAI_USE_VERTEXAI=TRUE              # Use Vertex AI (recommended)
MODEL=gemini-2.5-flash-lite                 # Or gemini-2.0-flash-preview, gemini-3-flash-preview
```

**Important Configuration Notes:**

- **GOOGLE_CLOUD_PROJECT**: Required - set this to your actual GCP project ID
- **SESSION_SERVICE_PROVIDER**: 
  - `in_memory` - Simple, no persistence (good for testing)
  - `vertex` - Vertex AI Session Service (requires implementation)
  - `db` - PostgreSQL database (requires running PostgreSQL)
- **EXAMPLE_STORE_NAME**: Optional - provides few-shot examples to improve agent responses

### 5. Authenticate with Google Cloud

Choose one of these methods:

**Option A: Service Account Key**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
```

**Option B: gcloud CLI**
```bash
gcloud auth application-default login
gcloud config set project your-project-id
```

### 6. Run the Application

You need to run both servers in separate terminal windows:

**Terminal 1: Backend Server**
```bash
source .venv/bin/activate
python sessions_server.py
```

The API server will start on http://localhost:8000

**Terminal 2: Web Client Server**
```bash
source .venv/bin/activate
python client_server.py
```

The web client will be available at http://localhost:8080

### 7. Access the Application

Open your browser and navigate to:
```
http://localhost:8080
```

You should see the chat interface. Start a conversation with the cloud tutor agent!

## Using the Application

1. **Start a Session**: The app automatically creates a session on your first message
2. **Ask Questions**: Type questions about GCP services, cloud architecture, etc.
3. **Watch Streaming**: Responses stream in real-time as the agent generates them
4. **Check Regions**: Ask about service availability (e.g., "Which regions support Cloud Run?")
5. **Session History**: View the conversation history in the session panel

## API Endpoints

- `GET /` - Home page with API information
- `POST /sessions` - Create a new session
- `POST /chat` - Send a message and receive streaming response
- `GET /examples` - List available examples from the example store
