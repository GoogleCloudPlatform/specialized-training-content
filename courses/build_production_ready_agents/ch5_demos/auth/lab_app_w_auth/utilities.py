"""Utility functions for the ADK agent server."""

import json
import logging
import re
import warnings

from starlette import responses

logger = logging.getLogger(__name__)


# ============================================================================
# Logging Configuration
# ============================================================================

class TruncateLogFilter(logging.Filter):
    """Custom filter to truncate long log messages for specified loggers."""
    def __init__(self, logger_names, max_total_length=150):
        super().__init__()
        self.logger_names = logger_names if isinstance(logger_names, list) else [logger_names]
        self.max_total_length = max_total_length
    
    def filter(self, record):
        if record.name in self.logger_names:
            message = record.getMessage()
            
            # Calculate the length of level:source: prefix
            # Format is "LEVEL:source:"
            prefix_length = len(record.levelname) + 1 + len(record.name) + 1  # +1 for each colon
            
            # Calculate max message length
            max_message_length = self.max_total_length - prefix_length
            
            if len(message) > max_message_length:
                # Calculate slice size: 2*slice + 3 <= max_message_length
                slice_size = (max_message_length - 3) // 2
                
                # Truncate message: first slice_size chars + "..." + last slice_size chars
                record.msg = message[:slice_size] + "..." + message[-slice_size:]
                record.args = ()
        return True


def configure_logging():
    """Configure logging for the application."""
    logging.basicConfig(level=logging.INFO)
    
    # Suppress experimental feature warnings from ADK
    warnings.filterwarnings("ignore", message=".*EXPERIMENTAL.*PROGRESSIVE_SSE_STREAMING.*")
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", message=".*experimental.*")
    
    # Apply filter to httpx and any other verbose loggers
    verbose_loggers = ["httpx", "google_adk.google.adk.models.google_llm"]
    truncate_filter = TruncateLogFilter(verbose_loggers, max_total_length=135)
    
    for logger_name in verbose_loggers:
        logging.getLogger(logger_name).addFilter(truncate_filter)


# GCP Services and their available regions
GCP_SERVICE_REGIONS = {
    "Compute Engine": [
        "us-central1", "us-east1", "us-west1", "us-west2", 
        "europe-west1", "europe-west4", "asia-east1", 
        "asia-southeast1", "australia-southeast1"
    ],
    "Cloud Storage": [
        "us-central1", "us-east1", "us-west1", "us-west2", 
        "europe-west1", "europe-west2", "europe-west4", 
        "asia-east1", "asia-southeast1", "asia-northeast1", 
        "australia-southeast1", "southamerica-east1"
    ],
    "BigQuery": [
        "us-central1", "us-east1", "us-west1", "us-west2", 
        "europe-west1", "europe-west4", "asia-east1", 
        "asia-southeast1", "australia-southeast1"
    ],
    "Cloud Run": [
        "us-central1", "us-east1", "us-west1", 
        "europe-west1", "europe-west4", "asia-east1", 
        "asia-northeast1"
    ],
    "Cloud Functions": [
        "us-central1", "us-east1", "us-west1", "us-west2", 
        "europe-west1", "europe-west2", "asia-east1", 
        "asia-northeast1"
    ],
    "Google Kubernetes Engine": [
        "us-central1", "us-east1", "us-west1", "us-west2", 
        "europe-west1", "europe-west4", "asia-east1", 
        "asia-southeast1", "australia-southeast1", 
        "northamerica-northeast1"
    ],
    "Cloud SQL": [
        "us-central1", "us-east1", "us-west1", 
        "europe-west1", "asia-east1", "asia-southeast1"
    ],
    "Cloud Pub/Sub": [
        "us-central1", "us-east1", "us-west1", "us-west2", 
        "europe-west1", "europe-west4", "asia-east1", 
        "asia-southeast1", "australia-southeast1", 
        "southamerica-east1"
    ],
    "Cloud Firestore": [
        "us-central1", "us-east1", "us-west1", 
        "europe-west1", "europe-west4", "asia-east1"
    ],
    "Cloud Logging": [
        "us-central1", "us-east1", "us-west1", "us-west2", 
        "europe-west1", "europe-west4", "europe-north1", 
        "asia-east1", "asia-southeast1", "asia-northeast1", 
        "australia-southeast1", "northamerica-northeast1", 
        "southamerica-east1"
    ],
    "Vertex AI": [
        "us-central1", "us-east1", "us-west1", "us-west4",
        "europe-west1", "europe-west4", "asia-east1",
        "asia-northeast1", "asia-southeast1"
    ],
    "Vertex AI Agent Engine": [
        "us-central1", "us-east1", "us-west1",
        "europe-west1", "asia-east1"
    ],
    "Gemini Enterprise": [
        "us-central1", "us-east1", "us-west1", "us-west4",
        "europe-west1", "europe-west4", "asia-east1",
        "asia-northeast1"
    ]
}


def make_json_serializable(obj):
    """
    Convert any object to a JSON-serializable format.
    Handles complex objects, dataclasses, and ADK response types.
    """
    # Handle None, basic types
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj
    
    # Handle lists
    if isinstance(obj, (list, tuple)):
        return [make_json_serializable(item) for item in obj]
    
    # Handle dicts
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    
    # Handle objects with __dict__
    if hasattr(obj, '__dict__'):
        return {k: make_json_serializable(v) for k, v in obj.__dict__.items()}
    
    # Fallback to string representation
    return str(obj)


def clean_json_response(text: str) -> str:
    """
    Removes potential JSON markdown formatting (e.g., ```json\n...\n```)
    from LLM responses to ensure valid JSON parsing.
    """
    text = re.sub(r"^```json\n", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n```$", "", text, flags=re.MULTILINE)
    return text.strip()


def create_event_summary(event, event_index, summary_length=50):
    """
    Create a comprehensive summary of an ADK event including tool calls and responses.
    Returns a dictionary suitable for client display.
    
    Args:
        event: The ADK event object to summarize
        event_index: The index of the event in the session
        summary_length: Optional length for text preview (default: 50)
    """
    event_summary = {
        "index": event_index,
        "type": type(event).__name__,
        "author": event.author
    }
    
    # Extract tool calls
    calls = event.get_function_calls()
    if calls:
        tool_calls = []
        for call in calls:
            tool_calls.append({
                "name": call.name,
                "args": call.args
            })
        event_summary["tool_calls"] = tool_calls
    
    # Extract tool responses
    responses = event.get_function_responses()
    if responses:
        tool_responses = []
        for response in responses:
            tool_responses.append({
                "name": response.name,
                "response": make_json_serializable(response.response)
            })
        event_summary["tool_responses"] = tool_responses
    
    # Check if it's a final response
    if hasattr(event, 'is_final_response'):
        try:
            event_summary["is_final_response"] = event.is_final_response()
        except Exception:
            pass
    
    # Extract content information
    if hasattr(event, "content") and event.content:
        if hasattr(event.content, "role"):
            event_summary["role"] = event.content.role
        
        if hasattr(event.content, "parts") and event.content.parts:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    text_preview = part.text[:summary_length] if len(part.text) > summary_length else part.text
                    event_summary["text_preview"] = text_preview
                    event_summary["text_length"] = len(part.text)
                    break
    
    return event_summary


def log_event(event):
    """Log comprehensive information about an ADK event using structured logging."""
    logger.info("-" * 80)
    logger.info("EVENT OBJECT")
    logger.info("-" * 80)
    
    event_data = {
        "event_type": type(event).__name__,
        "author": event.author
    }

    calls = event.get_function_calls()
    if calls:
        for call in calls:
            tool_name = call.name
            arguments = call.args # This is usually a dictionary
            event_data["tool_calls"] = f"Tool: {tool_name}, Args: {arguments}"

    responses = event.get_function_responses()
    if responses:
        for response in responses:
            tool_name = response.name
            result_dict = response.response # The dictionary returned by the tool
            event_data["tool_responses"] = f"Tool: {tool_name}, Response: {result_dict}"

    # Check if it's a final response
    if hasattr(event, 'is_final_response'):
        try:
            event_data["is_final_response"] = event.is_final_response()
        except Exception as e:
            event_data["is_final_response_error"] = str(e)
    
    # Extract content information
    if hasattr(event, "content") and event.content:
        event_data["content_type"] = type(event.content).__name__
        
        if hasattr(event.content, "role"):
            event_data["content_role"] = event.content.role
        
        if hasattr(event.content, "parts") and event.content.parts:
            event_data["parts_count"] = len(event.content.parts)
            event_data["parts"] = []
            
            for i, part in enumerate(event.content.parts):
                part_info = {"index": i}
                
                if hasattr(part, "text") and part.text:
                    text_preview = part.text[:100] if len(part.text) > 100 else part.text
                    part_info["text_preview"] = text_preview
                    part_info["text_length"] = len(part.text)
                    part_info["has_more"] = len(part.text) > 100
                
                event_data["parts"].append(part_info)
    
    # Log as structured JSON
    logger.info(json.dumps(event_data, indent=2))
    logger.info("-" * 80)


def log_session(session):
    """Log session object properties using structured logging."""
    logger.info("SESSION OBJECT")
    logger.info("-" * 80)
    
    if not session:
        logger.info(json.dumps({"session": None}, indent=2))
        logger.info("-" * 80)
        return
    
    session_data = {
        "session_id": session.id,
        "app_name": session.app_name,
        "user_id": session.user_id,
        "state": session.state,
        "events_count": len(session.events),
        "last_update_time": session.last_update_time,
        "events_summary": []
    }
    
    # Add summary of recent events (last 3)
    recent_events = session.events[-3:] if len(session.events) > 3 else session.events
    for i, evt in enumerate(recent_events):
        event_summary = {
            "index": len(session.events) - len(recent_events) + i,
            "type": type(evt).__name__,
            "text_preview": f"{evt.content.parts[0].text[:10]}..."  
        }
        if hasattr(evt, "content") and evt.content:
            if hasattr(evt.content, "role"):
                event_summary["role"] = evt.content.role
        session_data["events_summary"].append(event_summary)
    
    logger.info(json.dumps(session_data, indent=2))
    logger.info("-" * 80)


def get_client_url(base_url: str) -> str:
    """
    Convert the server base URL to the client URL by swapping port to 8080.
    
    Handles two patterns:
    - CloudShell URLs: https://8000-cs-xxx.cloudshell.dev/ -> https://8080-cs-xxx.cloudshell.dev/
    - Standard URLs: http://localhost:8000/ -> http://localhost:8080/
    
    Args:
        base_url: The base URL of the server
        
    Returns:
        The client URL with port 8080 and /client.html appended
    """
    base_url = base_url.rstrip('/')
    
    # Try CloudShell-style port prefix replacement first
    client_url = re.sub(r'://(\d{4})-', r'://8080-', base_url)
    
    # If no port prefix was found, try standard hostname:port replacement
    if client_url == base_url:
        client_url = re.sub(r':(\d{4})$', r':8080', base_url)
    
    return f"{client_url}/client.html"


def generate_home_page_html(client_url: str) -> str:
    """
    Generate the HTML for the server home page.
    
    Args:
        client_url: The URL to the client application
        
    Returns:
        HTML string for the home page
    """
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ADK Agent Server</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
                background: #fafafa;
                height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #1a1a1a;
            }}
            
            .container {{
                background: white;
                padding: 40px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                max-width: 600px;
                margin: 20px;
            }}
            
            h1 {{
                font-size: 28px;
                font-weight: 300;
                margin-bottom: 16px;
                letter-spacing: -0.5px;
                color: #1a1a1a;
            }}
            
            p {{
                color: #666;
                line-height: 1.5;
                margin-bottom: 16px;
                font-size: 14px;
            }}
            
            .button {{
                display: inline-block;
                padding: 12px 24px;
                background-color: #1a1a1a;
                color: white;
                text-decoration: none;
                border-radius: 4px;
                font-weight: 500;
                font-size: 14px;
                transition: background-color 0.2s;
                margin-top: 8px;
                cursor: pointer;
                border: none;
            }}
            
            .button:hover:not(:disabled) {{
                background-color: #333;
            }}
            
            .button:disabled {{
                background-color: #ccc;
                cursor: not-allowed;
            }}
            
            .countdown {{
                display: inline-block;
                margin-left: 12px;
                color: #666;
                font-size: 14px;
                font-weight: 500;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Agent Serving App</h1>
            <p>
                Welcome to the <strong>Building an ADK Agent with Session, Memory, and Example Services</strong> lab.
            </p>
            <p>
                This server provides the agent API endpoints. To interact with the agent, 
                please click the button below to open the client application.
            </p>
            <a href="{client_url}" target="_blank" id="clientButton" class="button">
                Open Client Application
            </a>
            <!-- <span id="countdown" class="countdown">Ready in 20 seconds...</span> -->
        </div>
        
        <script>
            /* COUNTDOWN TIMER DISABLED - uncomment to re-enable
            let timeRemaining = 20;
            const button = document.getElementById('clientButton');
            const countdownDisplay = document.getElementById('countdown');
            
            function updateCountdown() {{
                if (timeRemaining > 0) {{
                    countdownDisplay.textContent = `Ready in ${{timeRemaining}} second${{timeRemaining !== 1 ? 's' : ''}}...`;
                    timeRemaining--;
                    setTimeout(updateCountdown, 1000);
                }} else {{
                    countdownDisplay.textContent = '';
                    button.style.pointerEvents = 'auto';
                    button.style.backgroundColor = '#1a1a1a';
                }}
            }}
            
            // Start countdown when page loads
            updateCountdown();
            */
        </script>
    </body>
    </html>
    """

