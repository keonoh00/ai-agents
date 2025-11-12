import os

import dotenv
from google.adk.agents import Agent

from .ollama import OllamaLLM

dotenv.load_dotenv(dotenv_path="../../../.env")


MODEL = OllamaLLM(model="openai/gpt-oss:latest")


def get_weather(city: str) -> str:

    return f"The weather in {city} is 30 degrees."


def convert_unit(degrees: int):
    return f"That is {degrees} degrees Fahrenheit."


geo_agent = Agent(
    name="GeoAgent",
    instruction="You help the user with their related questions",
    model=MODEL.googleAdk(),
    description="Transfer to this agent when you have a question about geography",
)

agent = Agent(
    name="WeatherAgent",
    instruction="You help the user with their related questions",
    model=MODEL.googleAdk(),
    tools=[get_weather, convert_unit],
    sub_agents=[geo_agent],
)

root_agent = agent
