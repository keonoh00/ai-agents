from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from ollama_wrapper import OllamaLLM

from .prompt import VIDEO_ASSEMBLER_DESCRIPTION, VIDEO_ASSEMBLER_PROMPT
from .tools import assemble_video

MODEL = OllamaLLM(model="ollama/gpt-oss:latest").googleAdk()

video_assembler = Agent(
    name="VideoAssemblerAgent",
    model=MODEL,
    description=VIDEO_ASSEMBLER_DESCRIPTION,
    instruction=VIDEO_ASSEMBLER_PROMPT,
    output_key="video_assembler_output",
    tools=[
        assemble_video,
    ],
)
