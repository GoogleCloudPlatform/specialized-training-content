import requests
from fastmcp import FastMCP

mcp = FastMCP("Enterprise Support API")

@mcp.tool
def create_support_ticket(customer_id, issue, priority):
    # JSONPlaceholder is a free, public fake API for demos and testing.
    # The POST succeeds and echoes back the payload with a fake id,
    # but nothing is actually stored anywhere.
    response = requests.post(
        "https://jsonplaceholder.typicode.com/posts",
        json={"customer_id": customer_id, "issue": issue, "priority": priority})
    return response.json()

@mcp.resource("data://docs")
def api_docs():
    return "Enterprise Support API v2.0 docs..."

if __name__ == "__main__":
    # Port 8001 so this server doesn't collide with adk web's default port 8000.
    mcp.run(transport="http", port=8001)
