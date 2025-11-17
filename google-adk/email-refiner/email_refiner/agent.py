from google.adk.agents import Agent, LoopAgent
from google.adk.models.lite_llm import LiteLlm

from .prompt import (
    CLARITY_EDITOR_DESCRIPTION,
    CLARITY_EDITOR_INSTRUCTION,
    EMAIL_OPTIMIZER_DESCRIPTION,
    EMAIL_SYNTHESIZER_DESCRIPTION,
    EMAIL_SYNTHESIZER_INSTRUCTION,
    LITERARY_CRITIC_DESCRIPTION,
    LITERARY_CRITIC_INSTRUCTION,
    PERSUASION_STRATEGIST_DESCRIPTION,
    PERSUASION_STRATEGIST_INSTRUCTION,
    TONE_STYLIST_DESCRIPTION,
    TONE_STYLIST_INSTRUCTION,
)

MODEL = LiteLlm(model="openai/gpt-4o-mini")

clarity_agent = Agent(
    name="ClarityEditorAgent",
    description=CLARITY_EDITOR_DESCRIPTION,
    instruction=CLARITY_EDITOR_INSTRUCTION,
    output_key="clarity_output",
)

tone_stylist_agent = Agent(
    name="ToneStylistAgent",
    description=TONE_STYLIST_DESCRIPTION,
    instruction=TONE_STYLIST_INSTRUCTION,
    output_key="tone_output",
)

persuation_agent = Agent(
    name="PersuationAgent",
    description=PERSUASION_STRATEGIST_DESCRIPTION,
    instruction=PERSUASION_STRATEGIST_INSTRUCTION,
    output_key="persuation_output",
)

email_synthesizer_agent = Agent(
    name="EmailSynthesizerAgent",
    description=EMAIL_SYNTHESIZER_DESCRIPTION,
    instruction=EMAIL_SYNTHESIZER_INSTRUCTION,
    output_key="synthesized_output",
)

literary_critic_agent = Agent(
    name="LiteraryCriticAgent",
    description=LITERARY_CRITIC_DESCRIPTION,
    instruction=LITERARY_CRITIC_INSTRUCTION,
)

email_refiner_agent = LoopAgent(
    name="EmailRefinerAgent",
    description=EMAIL_OPTIMIZER_DESCRIPTION,
    sub_agents=[
        clarity_agent,
        tone_stylist_agent,
        persuation_agent,
        email_synthesizer_agent,
        literary_critic_agent,
    ],
)

root_agent = email_refiner_agent
