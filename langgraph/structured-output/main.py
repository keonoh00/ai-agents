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

    base_url = os.environ.get("GPU_BASE_URL") or os.environ.get("GPU_SERVER_URL")
    if not base_url:
        raise RuntimeError("Set GPU_BASE_URL to your GPU server.")

    extra_body = {
        "llm_config": {
            "temperature": 0.1,
            "max_tokens": 512,
            "top_p": 0.9,
            "repetition_penalty": 1.05,
        }
    }

    llm = init_chat_model(
        model=os.environ.get("GPU_MODEL", "gpt-oss:latest"),
        base_url=base_url,
        api_key=os.environ.get("GPU_API_KEY", "not-needed"),
        extra_body=extra_body,
    )

    """
    Actual JSON request body shape after `extra_body` is merged and
    `with_structured_output(NetworkSpecificationResponse)` binds the schema:

    {
      "model": "gpt-oss:latest",
      "messages": [
        {"role": "system", "content": "<SYSTEM_PROMPT>"},
        {"role": "user", "content": "<user_request>"}
      ],
      "llm_config": {
        "temperature": 0.1,
        "max_tokens": 512,
        "top_p": 0.9,
        "repetition_penalty": 1.05
      },
      "tools": [
        {
          "type": "function",
          "function": {
            "name": "NetworkSpecificationResponse",
            "description": "",
            "parameters": {
              "properties": {
                "risk": {
                  "description": "Risk level of the network modification",
                  "enum": ["high", "normal", "low"],
                  "type": "string"
                },
                "urgency": {
                  "description": "Urgency level of the network modification",
                  "enum": ["high", "normal", "low"],
                  "type": "string"
                },
                "commands": {
                  "description": "List of commands to execute for the network modification",
                  "items": {"type": "string"},
                  "type": "array"
                },
                "notes": {
                  "description": "Additional notes or considerations for the network modification",
                  "type": "string"
                }
              },
              "required": ["risk", "urgency", "commands", "notes"],
              "type": "object"
            }
          }
        }
      ],
      "tool_choice": {
        "type": "function",
        "function": {"name": "NetworkSpecificationResponse"}
      },
      "parallel_tool_calls": false
    }
    """

    return llm.with_structured_output(NetworkSpecificationResponse)


def chatbot(agent, user_request: str) -> NetworkSpecificationResponse:
    messages = [
        ("system", SYSTEM_PROMPT),
        ("user", user_request),
    ]
    return agent.invoke(messages)


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
