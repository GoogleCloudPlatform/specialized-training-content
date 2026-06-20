"""Utility functions for the ADK agent server."""

import json
import logging
import warnings

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

