# Vertex AI Agent Client (React)

A simple React client for interacting with Vertex AI agents through the cloudrun-proxy API. This client handles Server-Sent Events (SSE) from the `async_stream_query` iterator.

## Features

- 🚀 Real-time streaming responses from Vertex AI agents
- 💬 Clean, modern chat interface
- 📝 Markdown rendering for agent responses
- ⚡ Built with React + Vite for fast development
- 🔄 Session management with automatic creation

## Setup

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

The client will be available at `http://localhost:3000` and will proxy API requests to `http://localhost:8080`.

## Building for Production

1. Build the client:
```bash
npm run build
```

This will create optimized production files in the `../dist` directory, which the FastAPI server serves.

2. Start the FastAPI server:
```bash
cd ..
python main.py
```

The application will be available at `http://localhost:8080`.

## Architecture

- **Frontend**: React with Vite for fast development and optimized builds
- **Streaming**: Uses `@microsoft/fetch-event-source` for SSE with POST support
- **Markdown**: Uses `marked` library for rendering agent responses
- **API**: Proxies requests to the cloudrun-proxy FastAPI backend

## Event Handling

The client handles events from the Vertex AI `async_stream_query` iterator:

- `AgentThinkingEvent`: Agent processing events
- `ResponseChunkEvent`: Streaming response chunks
- `TextEvent`: Text content events
- Error events: Displayed in console

The event parser extracts text content from various event types and accumulates it for display.

## Configuration

Create a `.env` file (copy from `.env.example`) to configure:

- `VITE_API_URL`: API base URL (defaults to `/api` for proxied requests)

## Development

The Vite dev server includes a proxy configuration that forwards `/api/*` requests to `http://localhost:8080`, allowing you to develop the frontend without CORS issues.

Make sure the FastAPI server is running on port 8080 when developing.
