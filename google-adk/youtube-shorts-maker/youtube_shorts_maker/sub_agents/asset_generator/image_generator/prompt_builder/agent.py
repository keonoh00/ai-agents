from google.adk.agents import Agent
from ollama import OllamaLLM

from .model import PromptBuilderOutput
from .prompt import PROMPT_BUILDER_DESCRIPTION, PROMPT_BUILDER_PROMPT

llm = OllamaLLM(model="ollama/gpt-oss:latest").googleAdk()


prompt_builder_agent = Agent(
    name="PromptBuilderAgent",
    instruction=PROMPT_BUILDER_PROMPT,
    description=PROMPT_BUILDER_DESCRIPTION,
    model=llm,
    output_schema=PromptBuilderOutput,
    output_key="prompt_builder_output",
)
