# Creating an MCP Server with FastMCP

## Overview

This is example code, the tool and resource as implemented don't really do anything. The intent is to walk students through the MCP server code and the agent code.

## MCP Server

Super simple example of using FastMCP to define a networked MCP server.

When walking through `fast.py`, highlight the following:

- **FastMCP initialization** — A single line creates the server and gives it a name that clients can discover. This is all the boilerplate you need.
- **`@mcp.tool` decorator** — Show how any regular Python function becomes a callable tool just by adding the decorator. The function's parameters automatically become the tool's input schema, so there's no separate schema definition to maintain.
- **`@mcp.resource` decorator** — Contrast this with tools: resources are *read-only data* the agent can pull in for context (like documentation or config), not actions it can execute. The URI scheme (`data://docs`) is how the agent references it.
- **`mcp.run(transport="http", port=8000)`** — Point out that this single call starts a networked server. The transport choice (`http` vs `stdio`) is what makes this server accessible over the network rather than only to a local subprocess.

## Agent server

Very simple agent that uses McpToolset to connect to MCP server. No serving
app, so you would need to run in ADK API Server (or ADK Web).

When walking through `agent.py`, highlight the following:

- **`McpToolset` as a tool source** — Show how the agent's `tools` list doesn't contain individual tool definitions. Instead, it points to an MCP server via `McpToolset`, and the agent discovers available tools (and resources) at runtime. This is the key decoupling that MCP provides.
- **`StreamableHTTPConnectionParams`** — This is how the agent knows where to find the MCP server. Point out the URL (`http://127.0.0.1:8000/mcp`) and connect it back to the `mcp.run(transport="http", port=8000)` call in `fast.py` — one starts the server, the other connects to it.
- **Agent instruction references MCP capabilities** — The instruction mentions `create_support_ticket` and `api_docs` by name even though they aren't defined in this file. The agent will resolve them from the MCP server, so the instruction acts as guidance for *when* to use tools the agent discovers dynamically.
- **No serving layer** — Unlike a typical FastAPI app, there's no `app` object or route definitions here. This agent must be run through ADK's built-in server (`adk api_server` or `adk web`), which handles the chat UI and session management.