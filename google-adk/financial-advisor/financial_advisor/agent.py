import os

import dotenv
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from ollama import OllamaLLM

from .data_analyst import data_analyst
from .financial_analyst import financial_analyst
from .news_analyst import news_analyst
from .prompt import PROMPT

dotenv.load_dotenv(dotenv_path="../../../.env")


llm = OllamaLLM(model="ollama/gpt-oss:latest").googleAdk()


def save_advice_report():
    pass


agent = Agent(
    name="FinancialAdvisor",
    instruction=PROMPT,
    model=llm,
    tools=[
        AgentTool(agent=financial_analyst),
        AgentTool(agent=news_analyst),
        AgentTool(agent=data_analyst),
        save_advice_report,
    ],
)

root_agent = agent
