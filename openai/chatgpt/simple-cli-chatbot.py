# This is just a simple chatbot that uses the OpenAI SDK

import asyncio

import dotenv
from agents import Agent, ItemHelpers, Runner, function_tool
from agents.items import MessageOutputItem, ToolCallItem, ToolCallOutputItem

dotenv.load_dotenv()


@function_tool
def get_weather_tool(city: str) -> str:
    """
    Get the weather for a given city.

    Args:
      city: The city to get the weather for.

    Returns:
      The weather in the city.
    """
    return f"The weather in {city} is sunny."


agent = Agent(
    name="chatbot",
    instructions="You are a helpful assistant. Use tools when needed to answer questions.",
    tools=[get_weather_tool],
)


async def main():
    stream = Runner.run_streamed(
        agent, "What is the capital of France? and what is the weather?"
    )

    async for event in stream.stream_events():
        match event.type:
            case "raw_response_event":
                continue
            case "run_item_stream_event":
                item = event.item
                if isinstance(item, ToolCallItem):
                    if hasattr(item.raw_item, "model_dump"):
                        print(item.raw_item.model_dump())
                    else:
                        print(item.raw_item)
                elif isinstance(item, ToolCallOutputItem):
                    print(item.output)
                elif isinstance(item, MessageOutputItem):
                    print(ItemHelpers.text_message_output(item))


if __name__ == "__main__":
    asyncio.run(main())
