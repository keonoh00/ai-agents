from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from ollama import OllamaLLM

from .prompt import SHORTS_PRODUCER_DESCRIPTION, SHORTS_PRODUCER_PROMPT
from .sub_agents.content_planner.agent import content_planner

llm = OllamaLLM(model="ollama/gpt-oss:latest").googleAdk()
shorts_producer = Agent(
    name="ShortsProducerAgent",
    description=SHORTS_PRODUCER_DESCRIPTION,
    instruction=SHORTS_PRODUCER_PROMPT,
    model=llm,
    tools=[AgentTool(agent=content_planner)],
)

root_agent = shorts_producer
