import os
import sqlite3

import dotenv
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import interrupt

dotenv.load_dotenv("../../.env")


@tool
def get_human_feedback(poem: str):
    """
    Get human feedback on a poem.
    Use this to get feedback on a poem.
    The user will tell you if the poem is ready or if it needs more work.
    """
    response = interrupt({"poem": poem})
    return response["feedback"]


tools = [get_human_feedback]

# llm = init_chat_model("openai:gpt-4o-mini")
llm = init_chat_model(
    "ollama:gpt-oss:120b",
    base_url=os.environ.get("OLLAMA_BASE_URL"),
)
llm_with_tools = llm.bind_tools(tools)


class State(MessagesState):
    pass


def chatbot(state: State) -> State:
    response = llm_with_tools.invoke(
        f"""
    You are an expert at making poems.
                                     
    You are given a topic and need to write a poem about it.

    Use the `get_human_feedback` tool to get feedback on your poem.

    Only after the user says the poem is ready, you should return the poem.

    Here is the conversation history:
    {state['messages']}
    """
    )
    return {
        "messages": [response],
    }


tool_node = ToolNode(
    tools=tools,
)

graph_builder = StateGraph(State)

graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)

graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge("chatbot", END)

conn = sqlite3.connect("memory.db", check_same_thread=False)
memory = SqliteSaver(conn)

graph = graph_builder.compile(name="poet_agent")
