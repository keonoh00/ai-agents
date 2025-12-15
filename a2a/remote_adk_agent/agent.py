from dotenv import load_dotenv

load_dotenv(dotenv_path="../../.env")

from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm


def dummy_tool(hello: str):
    """Dummy Tool. Helps the agent"""
    return "world"


agent = Agent(
    name="HistoryHelperAgent",
    description="An agent that can help students with their history homework",
    model=LiteLlm("openai/gpt-4o"),
    tools=[dummy_tool],
)

app = to_a2a(agent, port=8001)
