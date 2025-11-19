from google.adk.agents import Agent
from google.adk.apps.app import App
from google.adk.tools.bigquery import BigQueryCredentialsConfig, BigQueryToolset
import google.auth
import dotenv
import random
import time

dotenv.load_dotenv()

credentials, _ = google.auth.default()
credentials_config = BigQueryCredentialsConfig(credentials=credentials)
bigquery_toolset = BigQueryToolset(
  credentials_config=credentials_config
)

PROJECT_ID = 'qwiklabs-gcp-04-5b35cde8e0a8'

def possible_bottleneck() -> dict[str,int]:
    """
    10% of the time adds a random delay between 1 and 5 seconds to the response.

    Args: None

    Returns:
        A dict with the delay in milliseconds for logging purposes. For example: {'delay', 100}
    """

    delay = float(random.randint(0,5000)/1000)
    if random.random() < 0.1:
      time.sleep(delay)
    else:
      delay = 0

    return {"delay": int(delay*1000)}

root_agent = Agent(
 model="gemini-2.5-flash",
 name="bigquery_agent",
 description="Agent that answers questions about BigQuery data by executing SQL queries.",
 instruction=(
     f"""
       You are a BigQuery data analysis agent.
       You are able to answer questions on data stored in project-id: '{PROJECT_ID}' on the `ecommerce` dataset.
       Before every request to the bigquery_toolset tools, use the possible_bottleneck tool to add a random delay between 0 and 1000 milliseconds.
     """
 ),
 tools=[bigquery_toolset, possible_bottleneck]
)

app = App(root_agent=root_agent, name="app")