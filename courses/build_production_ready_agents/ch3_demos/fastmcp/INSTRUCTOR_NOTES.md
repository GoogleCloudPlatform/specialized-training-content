# Creating an MCP Server with FastMCP

## Overview

This is example code — `create_support_ticket` is stubbed out and doesn't call a real backend. The intent is to walk students through the MCP server code and the agent code.

This file is named `INSTRUCTOR_NOTES.md` rather than `README.md` on purpose: ADK Web reads a `README.md` in the agent directory and renders it in the UI on session load, which would put these notes in front of students.

## MCP Server

Super simple example of using FastMCP to define a networked MCP server.

When walking through `fast.py`, highlight the following:

- **FastMCP initialization** — A single line creates the server and gives it a name that clients can discover. This is all the boilerplate you need.
- **`@mcp.tool` decorator** — Show how any regular Python function becomes a callable tool just by adding the decorator. The function's parameters automatically become the tool's input schema, so there's no separate schema definition to maintain.
- **`@mcp.resource` decorator** — Contrast this with tools: resources are *read-only data* the agent can pull in for context (like documentation or config), not actions it can execute. The URI scheme (`data://docs`) is how the agent references it. Here the resource holds the `customer_id` format and the P0–P3 priority definitions — reference data the agent needs *before* it can fill in the tool's arguments correctly.
- **`mcp.run(transport="http", port=8000)`** — Point out that this single call starts a networked server. The transport choice (`http` vs `stdio`) is what makes this server accessible over the network rather than only to a local subprocess.

## Agent server

Very simple agent that uses McpToolset to connect to MCP server. No serving
app, so you would need to run in ADK API Server (or ADK Web).

When walking through `agent.py`, highlight the following:

- **`McpToolset` as a tool source** — Show how the agent's `tools` list doesn't contain individual tool definitions. Instead, it points to an MCP server via `McpToolset`, and the agent discovers available tools (and resources) at runtime. This is the key decoupling that MCP provides.
- **`StreamableHTTPConnectionParams`** — This is how the agent knows where to find the MCP server. Point out the URL (`http://127.0.0.1:8000/mcp`) and connect it back to the `mcp.run(transport="http", port=8000)` call in `fast.py` — one starts the server, the other connects to it.
- **`use_mcp_resources=True`** — Resources are opt-in; this flag defaults to `False`. Without it the agent sees only the MCP server's *tools*, and asking about the docs gets you a confident hallucination instead of a fetch. Setting it adds ADK's `load_mcp_resource` tool and injects the server's resource names into the prompt.
- **Agent instruction references MCP capabilities** — The instruction mentions `create_support_ticket` and `api_docs` by name even though they aren't defined in this file. The agent will resolve them from the MCP server, so the instruction acts as guidance for *when* to use tools the agent discovers dynamically.
- **Resource-then-tool sequencing** — The instruction makes the agent read `api_docs` *before* calling `create_support_ticket`. Watch the Events tab: `load_mcp_resource` fires first, then `create_support_ticket` with a priority the agent justifies from the fetched text. That ordering is the whole point of the resource/tool split — context first, action second.
- **No serving layer** — Unlike a typical FastAPI app, there's no `app` object or route definitions here. This agent must be run through ADK's built-in server (`adk api_server` or `adk web`), which handles the chat UI and session management.