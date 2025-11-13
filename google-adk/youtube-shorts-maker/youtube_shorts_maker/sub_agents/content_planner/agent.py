from google.adk.agents import Agent
from ollama_wrapper import OllamaLLM

from .model import ContentPlanOutput
from .prompt import CONTENT_PLANNER_DESCRIPTION, CONTENT_PLANNER_PROMPT

model = OllamaLLM(model="ollama/gpt-oss:latest").googleAdk()

content_planner = Agent(
    name="ContentPlannerAgent",
    description=CONTENT_PLANNER_DESCRIPTION,
    instruction=CONTENT_PLANNER_PROMPT,
    model=model,
    output_schema=ContentPlanOutput,
    output_key="content_planner_output",
)
