import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor

load_dotenv(dotenv_path="../../.env")

MODEL = "ollama:gpt-oss"

history_agent = create_react_agent(
    model=MODEL,
    tools=[],
    name="history_agent",
    prompt="You are a history expert. You only answer questions about history.",
)

geography_agent = create_react_agent(
    model=MODEL,
    tools=[],
    name="geography_agent",
    prompt="You are a geography expert. You only answer questions about geography.",
)

math_agent = create_react_agent(
    model=MODEL,
    tools=[],
    name="math_agent",
    prompt="You are a math expert. You only answer questions about math.",
)

philosophy_agent = create_react_agent(
    model=MODEL,
    tools=[],
    name="philosophy_agent",
    prompt="You are a philosophy expert. You only answer questions about philosophy.",
)

supervisor = create_supervisor(
    agents=[history_agent, math_agent, geography_agent, philosophy_agent],
    model=init_chat_model(
        model=MODEL,
        base_url=os.environ.get("OLLAMA_BASE_URL"),
        prompt="""
        You are a supervisor that routes student questions to the appropriate subject expert. 
        You manage a history agent, geography agent, maths agent, and philosophy agent. 
        Analyze the student's question and assign it to the correct expert based on the subject matter:
            - history_agent: For historical events, dates, historical figures
            - geography_agent: For locations, rivers, mountains, countries
            - maths_agent: For mathematics, calculations, algebra, geometry
            - philosophy_agent: For philosophical concepts, ethics, logic
        """,
    ),
).compile()


if __name__ == "__main__":
    questions = [
        "What is the capital of France and what river runs through it?",
        "What is 15% of 240?",
        "Tell me about the Battle of Waterloo",
        "What are the highest mountains in Asia?",
        "If I have a rectangle with length 8 and width 5, what is its area and perimeter?",
        "Who was Alexander the Great?",
        "What countries border Switzerland?",
        "Solve for x: 2x + 10 = 30",
    ]

    for question in questions:
        result = supervisor.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": question,
                    }
                ],
            },
        )
        if result["messages"]:
            for message in result["messages"]:
                message.pretty_print()
