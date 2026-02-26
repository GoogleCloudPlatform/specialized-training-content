import vertexai

resource_name = "projects/906184221373/locations/us-central1/reasoningEngines/5891248172809846784"
client = vertexai.Client(project="906184221373", location="us-central1")
agent = client.agent_engines.get(name=resource_name)

# Create a session
session = agent.async_create_session(user_id="debug-user")
print("Session:", type(session), repr(session))
print()

session_id = session["id"]

# Stream a query and print raw events
print("--- Events ---")
for event in agent.async_stream_query(
    user_id="debug-user",
    session_id=session_id,
    message="list tables please",
):
    print(f"TYPE: {type(event)}")
    print(f"REPR: {repr(event)[:500]}")
    if isinstance(event, dict):
        print(f"KEYS: {list(event.keys())}")
    elif hasattr(event, "__dict__"):
        print(f"ATTRS: {list(vars(event).keys())}")
    print()
