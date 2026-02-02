# Simple Demo for user auth with MCP Tools

## Overview

1. Agent definition is embedded in server
2. Agent uses helper function to return McpToolset with auth config
3. If user asks agent to do something that triggers too, it invokes auth flows
4. Remote MCP tool is Google's managed MCP tool for BigQuery

## Setup

1. Create an OAuth Desktop client (could use Web and configure redirect URIs)
2. Change directories to `ch3_demos\oauth`
3. Create a `.env` file from the .env.example
4. Populate the missing values
5. Create a virtual environment, activate it, and install requirements (in requirements.txt)

## Walk through code

1. You can scan through the first 100 lines of the server code to see how tool config (with auth options) is done
2. You can walk through key sections of the client to show how OAuth flow is presented

## Demo

1. In **oauth** directory, run server with `python server.py`
2. Open a second terminal window and change directories to the **oauth** directory
3. Run `python -m http.server 8080`
4. Open your Web browser to localhost:8080 and test it out