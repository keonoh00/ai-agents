from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.adk.tools.agent_tool import AgentTool
from google.genai import types
from ollama_wrapper import OllamaLLM

from .prompt import SHORTS_PRODUCER_DESCRIPTION, SHORTS_PRODUCER_PROMPT
from .sub_agents.asset_generator.agent import asset_generator
from .sub_agents.content_planner.agent import content_planner
from .sub_agents.video_assembler.agent import video_assembler


def before_model_callback(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
):

    history = llm_request.contents
    last_message = history[-1]
    if last_message.role == "user" and last_message.parts:
        text = last_message.parts[0].text
        if text and "hummus" in text:
            return LlmResponse(
                content=types.Content(
                    parts=[types.Part(text="Sorry, I cannot help you with that...")],
                    role="model",
                )
            )

    return None


llm = OllamaLLM(model="ollama/gpt-oss:latest").googleAdk()

shorts_producer = Agent(
    name="ShortsProducerAgent",
    description=SHORTS_PRODUCER_DESCRIPTION,
    instruction=SHORTS_PRODUCER_PROMPT,
    model=llm,
    tools=[
        AgentTool(agent=content_planner),
        AgentTool(agent=asset_generator),
        AgentTool(agent=video_assembler),
    ],
    before_model_callback=before_model_callback,
)

root_agent = shorts_producer
