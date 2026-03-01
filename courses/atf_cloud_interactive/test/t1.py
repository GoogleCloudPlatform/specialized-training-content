import asyncio

import vertexai

resource_name = "projects/906184221373/locations/us-central1/reasoningEngines/1068579067151777792"
client = vertexai.Client(project="906184221373", location="us-central1")
agent = client.agent_engines.get(name=resource_name)


async def main():
    # Create a session
    session = await agent.async_create_session(user_id="debug-user")
    print("Session:", type(session), repr(session))
    print()

    session_id = session["id"]

    # Stream a query and print raw events
    print("--- Events ---")
    async for event in agent.async_stream_query(
        user_id="debug-user",
        session_id=session_id,
        message="tell me about the customers table",
    ):
        print(f"TYPE: {type(event)}")
        print(f"REPR: {repr(event)[:500]}")
        if isinstance(event, dict):
            print(f"KEYS: {list(event.keys())}")
        elif hasattr(event, "__dict__"):
            print(f"ATTRS: {list(vars(event).keys())}")
        print()


asyncio.run(main())