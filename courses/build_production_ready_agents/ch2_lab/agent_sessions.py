from google.adk import Agent
from utilities import GCP_SERVICE_REGIONS


def check_gcp_service_availability(service_name: str):
    """
    Check GCP service availability across regions.

    Args:
        service_name (str): The name of the GCP service (e.g., 'Compute Engine', 'Cloud Storage').
    
    Returns:
        dict: A JSON payload with the service name and list of available regions.
    """
    canonical = {k.lower(): k for k in GCP_SERVICE_REGIONS}
    key = canonical.get(service_name.strip().lower())
    if key is None:
        return {"service": service_name, "error": "Service not found",
                "available_services": list(GCP_SERVICE_REGIONS)}
    return {"service": key, "available_regions": GCP_SERVICE_REGIONS[key],
            "region_count": len(GCP_SERVICE_REGIONS[key])}

# Create the agent
root_agent = Agent(
    name="gemini_cloud_tutor",
    model="gemini-3.5-flash",
    instruction="""
    You're my cloud technology tutor, helping me develop a solid understanding of Google Cloud concepts and products. 
    You're working to make sure I understand the concept and the application.
    When providing information about Google Cloud services, be sure to include information about availability across different regions using the check_gcp_service_availability tool.
    check_gcp_service_availability is the only tool you have access to.
    """,
    tools=[check_gcp_service_availability]
)