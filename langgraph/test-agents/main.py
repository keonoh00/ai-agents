from typing import List, Literal, NotRequired

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict


class EmailState(TypedDict):
    email: str
    category: Literal["spam", "normal", "urgent"]
    priority_score: int

    response: str


def categorize_email(state: EmailState) -> EmailState:
    email = state.get("email", "").lower()

    if "urgent" in email or "asap" in email:
        category = "urgent"
    elif "offer" in email or "discount" in email:
        category = "urgent"
    else:
        category = "normal"

    return {"category": category}


def assign_priority(state: EmailState) -> EmailState:
    scores = {
        "urgent": 10,
        "normal": 5,
        "spam": 1,
    }

    return {
        "priority_score": scores[state["category"]],
    }


def draft_response(state: EmailState) -> EmailState:
    responses = {
        "urgent": "I will answer you as fast as I can",
        "normal": "I will get back to you soon",
        "spam": "Go away~",
    }

    return {
        "response": responses[state["category"]],
    }


graph_builder = StateGraph(EmailState)

graph_builder.add_node("categorize_email", categorize_email)
graph_builder.add_node("assign_priority", assign_priority)
graph_builder.add_node("draft_response", draft_response)

graph_builder.add_edge(START, "categorize_email")
graph_builder.add_edge("categorize_email", "assign_priority")
graph_builder.add_edge("assign_priority", "draft_response")
graph_builder.add_edge("draft_response", END)

graph = graph_builder.compile()

result = graph.invoke({"email": "I need to talk to you urgently"})
print(result)
