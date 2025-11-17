from google.adk.agents import Agent
from ollama_wrapper import OllamaLLM

from .prompt import IMAGE_BUILDER_DESCRIPTION, IMAGE_BUILDER_PROMPT
from .tools import generate_images

llm = OllamaLLM(model="ollama/gpt-oss:latest").googleAdk()

image_builder_agent = Agent(
    name="ImageBuilderAgent",
    description=IMAGE_BUILDER_DESCRIPTION,
    instruction=IMAGE_BUILDER_PROMPT,
    model=llm,
    tools=[generate_images],
)
