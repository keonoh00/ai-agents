from agents.classification_agent import classification_agent
from agents.feynman_agent import feynman_agent
from agents.quiz_agent import quiz_agent
from agents.teacher_agent import teacher_agent
from langgraph.graph import END, START, MessagesState, StateGraph


class TutorState(MessagesState):
    current_agent: str


def router_check(state: TutorState):
    current_agent = state.get(
        "current_agent",
        "classification_agent",
    )

    return current_agent


graph_builder = StateGraph(TutorState)

graph_builder.add_node(
    "classification_agent",
    classification_agent,
    destinations=(
        "teacher_agent",
        "feynman_agent",
        "quiz_agent",
    ),
)
graph_builder.add_node("teacher_agent", teacher_agent)
graph_builder.add_node("feynman_agent", feynman_agent)
graph_builder.add_node("quiz_agent", quiz_agent)


graph_builder.add_conditional_edges(
    START,
    router_check,
    [
        "quiz_agent",
        "teacher_agent",
        "feynman_agent",
        "classification_agent",
    ],
)
graph_builder.add_edge("classification_agent", END)

graph = graph_builder.compile()
