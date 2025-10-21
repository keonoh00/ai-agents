import json
from typing import Callable, Dict, List

from openai.types.chat import ChatCompletionMessage, ChatCompletionToolUnionParam

import openai

client = openai.OpenAI()
messages = []


def get_weather(city):
    return f"{city} is 33 degrees celcius."


FUNCTION_MAP: Dict[str, Callable] = {
    "get_weather": get_weather,
}

TOOLS: List[ChatCompletionToolUnionParam] = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "A function to get the weather of a city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The name of the city to get the weather of.",
                    }
                },
                "required": ["city"],
            },
        },
    }
]


def process_ai_response(
    message: ChatCompletionMessage,
):
    if message.tool_calls:
        messages.append(
            {
                "role": "assistant",
                "content": message.content or "",
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in message.tool_calls
                ],
            }
        )

        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            arguments = tool_call.function.arguments

            print(f"Calling function: {function_name} with {arguments}")

            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {}

            function_to_run = FUNCTION_MAP.get(function_name)

            if function_to_run is not None:
                result = function_to_run(**arguments)
                print(
                    f"Ran {function_name} with args {arguments} for a result of {result}"
                )
            else:
                result = f"Function '{function_name}' not found."
                print(result)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": result,
                }
            )

        call_ai()
    else:
        messages.append({"role": "assistant", "content": message.content})
        print(f"AI: {message.content}")


def call_ai():
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=TOOLS,
    )
    process_ai_response(response.choices[0].message)


def main() -> None:
    while True:
        message = input("Send a message to the LLM...")
        if message == "quit" or message == "q":
            break
        else:
            messages.append({"role": "user", "content": message})
            print(f"User: {message}")
            call_ai()
