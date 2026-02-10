from google.adk import Agent
from google.adk.tools import google_search
from utilities import GCP_SERVICE_REGIONS


def check_gcp_service_availability(service_name: str):
    """
    Check GCP service availability across regions.

    Args:
        service_name (str): The name of the GCP service (e.g., 'Compute Engine', 'Cloud Storage').
    
    Returns:
        dict: A JSON payload with the service name and list of available regions.
    """
    if service_name in GCP_SERVICE_REGIONS:
        return {
            "service": service_name,
            "available_regions": GCP_SERVICE_REGIONS[service_name],
            "region_count": len(GCP_SERVICE_REGIONS[service_name])
        }
    else:
        return {
            "service": service_name,
            "error": "Service not found",
            "available_services": list(GCP_SERVICE_REGIONS.keys())
        }

# Create the agent
root_agent = Agent(
    name="gemini_cloud_tutor",
    model="gemini-2.5-flash-lite",
    instruction="""
    You're my cloud technology tutor, helping me develop a solid understanding of Google Cloud concepts and products. 
    You're working to make sure I understand the concept and the application.
    When providing information about Google Cloud services, be sure to include information about availability across different regions using the check_gcp_service_availability tool.
    """,
    tools=[check_gcp_service_availability]
)