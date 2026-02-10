import requests
from fastmcp import FastMCP

mcp = FastMCP("Enterprise Support API")

@mcp.tool
def create_support_ticket(customer_id, issue, priority):
    response = requests.post(
        "https://buganizer.internal/posts",
        json={"customer_id": customer_id, "issue": issue, "priority": priority})
    return response.json()

@mcp.resource("data://docs")
def api_docs():
    return "Enterprise Support API v2.0 docs..."

if __name__ == "__main__":
    mcp.run(transport="http", port=8000)