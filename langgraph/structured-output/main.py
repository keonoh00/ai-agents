import os
from typing import List, Literal

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field


class NetworkSpecificationResponse(BaseModel):
    risk: Literal["high", "normal", "low"] = Field(
        description="Risk level of the network modification"
    )
    urgency: Literal["high", "normal", "low"] = Field(
        description="Urgency level of the network modification"
    )
    commands: List[str] = Field(
        description="List of commands to execute for the network modification"
    )
    notes: str = Field(
        description="Additional notes or considerations for the network modification"
    )


SYSTEM_PROMPT = """
You are a network administrator responsible for managing and maintaining the organization's network infrastructure.
Your task is to analyze the user request for the network problem and provide a structured response that includes the risk level, urgency level, specific commands to execute, and any additional notes or considerations.
"""


def build_agent():
    load_dotenv(dotenv_path="../../.env")

    llm = init_chat_model(
        "ollama:gpt-oss:latest",
        base_url=os.environ.get("OLLAMA_BASE_URL"),
        # headers={"API-Key": "langgraph-structured-output"},
    )

    return llm.with_structured_output(NetworkSpecificationResponse)


def chatbot(agent, user_request: str) -> NetworkSpecificationResponse:
    result = agent.invoke(f"{SYSTEM_PROMPT}\n\nUser request:\n{user_request}")
    return NetworkSpecificationResponse.model_validate(result)


def main():
    agent = build_agent()

    while True:
        user_request = input("Request: ").strip()

        if user_request.lower() in {"exit", "quit"}:
            break

        if not user_request:
            continue

        response = chatbot(agent, user_request)
        print(response.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
