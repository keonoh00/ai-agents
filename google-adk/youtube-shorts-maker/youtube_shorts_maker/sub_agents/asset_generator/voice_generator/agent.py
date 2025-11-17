from google.adk.agents import Agent
from ollama_wrapper import OllamaLLM

from .prompt import VOICE_GENERATOR_DESCRIPTION, VOICE_GENERATOR_PROMPT
from .tools import generate_narrations

llm = OllamaLLM(model="ollama/gpt-oss:latest").googleAdk()


voice_generator_agent = Agent(
    name="VoiceGeneratorAgent",
    description=VOICE_GENERATOR_DESCRIPTION,
    instruction=VOICE_GENERATOR_PROMPT,
    model=llm,
    tools=[generate_narrations],
)
