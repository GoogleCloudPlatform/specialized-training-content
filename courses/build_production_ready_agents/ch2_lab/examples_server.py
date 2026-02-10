"""
ADK Agent API Server with Example Store Integration

A FastAPI server that retrieves relevant examples from Example Store,
constructs dynamic prompts, and returns agent responses with streaming support.
"""

import asyncio
import json
import logging
import os
import sys

import vertexai
from agent_examples import root_agent
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from google.adk.agents import Agent
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import InMemoryRunner, Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from utilities import (clean_json_response, configure_logging,
                       create_event_summary, generate_home_page_html,
                       get_client_url, log_event, log_session)
from vertexai.preview import example_stores

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
EXAMPLE_STORE_NAME = os.getenv("EXAMPLE_STORE_NAME", "")


# ============================================================================
# ADK Session Setup
# ============================================================================

# Create the session service (using in-memory for simplicity with examples)
session_service = InMemorySessionService()
logger.info(f"Using SESSION_SERVICE_PROVIDER: in_memory (for examples demo)")


# ============================================================================
# Example Store Setup
# ============================================================================

# Initialize Vertex AI
vertexai.init(
    project=GOOGLE_CLOUD_PROJECT,
    location=AGENT_ENGINE_LOCATION
)

# Connect to the Example Store
if not EXAMPLE_STORE_NAME:
    logger.warning("EXAMPLE_STORE_NAME not set in .env - example retrieval will be disabled")
    example_store = None
else:
    try:
        example_store = example_stores.ExampleStore(EXAMPLE_STORE_NAME)
        logger.info(f"Connected to Example Store: {EXAMPLE_STORE_NAME}")
    except Exception as e:
        logger.error(f"Failed to connect to Example Store: {e}")
        example_store = None


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

app = FastAPI(title="ADK Agent Server with Examples", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
                detail=f"Invalid session_id: '{session_id}' not found for user '{user_id}'."
            )
    return session, session_id


def summarize_session_events(session):
    """Return a list of event summaries for a session."""
    return [create_event_summary(evt, idx, 200) for idx, evt in enumerate(session.events)]


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
    """Return a summary dict for the session."""
    return {
        "session_id": session.id,
        "app_name": session.app_name,
        "user_id": session.user_id,
        "state": session.state,
        "events_count": len(session.events),
        "last_update_time": int(session.last_update_time * 1000) if session.last_update_time else None
    }


def format_examples_for_prompt(examples_results: list) -> str:
    """
    Format retrieved examples into a prompt string.
    
    Args:
        examples_results: List of example results from example_store.search_examples()
        
    Returns:
        Formatted string containing examples for the prompt
    """
    if not examples_results:
        return ""
    
    examples_preamble = """<EXAMPLES>
The following are examples of user queries and model responses. Use these as guidance for your response.

Begin few-shot examples:
"""
    
    examples_postamble = """
End few-shot examples.
</EXAMPLES>

Now, using the examples above as guidance, respond to the following conversation:
"""
    
    formatted_examples = []
    
    for idx, result in enumerate(examples_results, 1):
        example_data = result.get("example", {})
        stored_example = example_data.get("stored_contents_example", {})
        contents_example = stored_example.get("contents_example", {})
        
        search_key = stored_example.get("search_key", "")
        contents = contents_example.get("contents", [])
        expected_contents = contents_example.get("expected_contents", [])
        
        example_str = f"\n--- EXAMPLE {idx} ---\n"
        example_str += f"Query: {search_key}\n\n"
        
        # Format contents (user messages)
        for content in contents:
            role = content.get("role", "user")
            parts = content.get("parts", [])
            for part in parts:
                if "text" in part:
                    example_str += f"{role.upper()}: {part['text']}\n"
        
        # Format expected contents (model responses)
        for expected in expected_contents:
            content_obj = expected.get("content", {})
            role = content_obj.get("role", "model")
            parts = content_obj.get("parts", [])
            
            for part in parts:
                if "text" in part:
                    example_str += f"{role.upper()}: {part['text']}\n"
                elif "functionCall" in part:
                    func_call = part["functionCall"]
                    example_str += f"FUNCTION_CALL: {func_call.get('name')}({func_call.get('args', {})})\n"
                elif "functionResponse" in part:
                    func_resp = part["functionResponse"]
                    example_str += f"FUNCTION_RESPONSE: {func_resp.get('name')} -> {func_resp.get('response', {})}\n"
        
        formatted_examples.append(example_str)
    
    return examples_preamble + "\n".join(formatted_examples) + examples_postamble


async def retrieve_relevant_examples(
    query_text: str,
    top_k: int = 2,
    min_similarity: float = 0.6
) -> tuple[list, str]:
    """
    Search for and filter relevant examples from the Example Store.
    
    Args:
        query_text: The user query to search for
        top_k: Number of examples to retrieve
        min_similarity: Minimum similarity score threshold
        
    Returns:
        Tuple of (filtered_examples_list, formatted_prompt_string)
    """
    relevant_examples = []
    examples_prompt = ""
    
    if not example_store:
        logger.info("Example Store not available, proceeding without examples")
        return relevant_examples, examples_prompt
    
    try:
        logger.info(f"Searching for examples relevant to: {query_text}")
        search_results = example_store.search_examples(
            {"stored_contents_example_key": query_text},
            top_k=top_k
        )
        
        # Extract results and filter by similarity score
        all_results = search_results.get("results", [])
        logger.info(f"Retrieved {len(all_results)} total examples from search")
        
        # Filter based on similarity score threshold
        for result in all_results:
            similarity_score = result.get("similarity_score", 0.0)
            
            if similarity_score > min_similarity:
                result_json = json.dumps(result, indent=2)
                logging.info(f"search_key: {result['example']['stored_contents_example']['search_key']}")
                relevant_examples.append(result)
                logger.info(f"Including example with similarity score: {similarity_score:.3f}")
            else:
                logger.info(f"Filtering out example with low similarity score: {similarity_score:.3f}")
        
        logger.info(f"After filtering: {len(relevant_examples)} examples with score > {min_similarity}")
        
        # Format examples for the prompt
        if relevant_examples:
            examples_prompt = format_examples_for_prompt(relevant_examples)
            # print(f"Examples Prompt:\n{examples_prompt}")
    except Exception as e:
        logger.error(f"Error retrieving examples: {e}", exc_info=True)
    
    return relevant_examples, examples_prompt


# ============================================================================
# API Endpoints
# ============================================================================

@app.post("/sessions")
async def create_session(request: dict):
    """Create a new session for a user."""
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=request["user_id"],
        state=request.get("initial_state", {})
    )
    
    return {
        "session_id": session.id,
        "user_id": session.user_id,
        "session_card": build_session_card_data(session)
    }


@app.post("/chat")
async def chat(request: dict):
    """Send a message to the agent and get a streaming response with session updates."""

    session_id = request.get("session_id")
    user_id = request["user_id"]
    user_message_text = request["message"]
    
    session, session_id = await get_or_create_session(user_id, session_id)

    # Search for relevant examples
    relevant_examples, examples_prompt = await retrieve_relevant_examples(
        query_text=user_message_text,
        top_k=2,
        min_similarity=0.6
    )

    prompt = f"{examples_prompt}\n{user_message_text}"

    user_message = types.Content(
        role="user",
        parts=[types.Part(text=prompt)]
    )

    async def event_generator():
        """Generate SSE events for session cards and streaming response chunks."""
        accumulated_text = ""
        event_index = 0

        try:
            # Send initial session card
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
                            chunk_text = part.text
                            accumulated_text += chunk_text

                            chunk_data = {
                                "type": "response_chunk",
                                "text": chunk_text,
                                "is_final": False
                            }
                            yield f"data: {json.dumps(chunk_data)}\n\n"

                if event.is_final_response():
                    break

            # Get final session state
            updated_session = await session_service.get_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id
            )

            # Send final session card
            final_session_card = build_session_card_data(updated_session)
            yield f"data: {json.dumps(final_session_card)}\n\n"

            session_summary = build_session_summary(updated_session)

            if not accumulated_text:
                logger.error("Agent did not produce any text response")
                error_data = {
                    "type": "error",
                    "message": "Agent did not produce any text response."
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                return

            # Send final completion event
            completion_data = {
                "type": "response_chunk",
                "text": "",
                "is_final": True,
                "session": session_summary,
                "examples_used": len(relevant_examples)
            }
            yield f"data: {json.dumps(completion_data)}\n\n"
            
        except Exception as e:
            logger.error(f"Error during agent execution: {str(e)}", exc_info=True)
            
            error_data = {
                "type": "error",
                "message": f"Agent execution failed: {str(e)}"
            }
            yield f"data: {json.dumps(error_data)}\n\n"
            
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
    """Home page with link to client application."""
    client_url = get_client_url(str(request.base_url))
    return HTMLResponse(content=generate_home_page_html(client_url))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "examples_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
