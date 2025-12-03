import pytest
from langgraph.graph.state import RunnableConfig
from main import graph

config: RunnableConfig = {
    "configurable": {
        "thread_id": "1",
    }
}


@pytest.mark.parametrize(
    "email, expected_category, min_score, max_score",
    [
        ("this is urgent!", "urgent", 8, 10),
        ("i wanna talk to you", "normal", 4, 7),
        ("i have an offer for you", "spam", 1, 3),
    ],
)
def test_full_graph(email, expected_category, min_score, max_score):
    result = graph.invoke(
        {
            "email": email,
        },
        config=config,
    )

    assert result["category"] == expected_category
    assert min_score <= result["priority_score"] <= max_score


def test_individual_node():
    # Categorize email
    result = graph.nodes["categorize_email"].invoke(
        {
            "email": "Check out this offer",
        }
    )
    assert result["category"] == "spam"

    # Assign priority
    result = graph.nodes["assign_priority"].invoke({"category": "spam"})
    assert result["priority_score"] == 1

    # Draft response
    # result = graph.nodes["draft_response"].invoke({"category": "spam"})
    # assert "Go away" in result["response"]


def test_partial_execution():

    graph.update_state(
        config=config,
        values={
            "email": "please checkout this offer",
            "category": "spam",
        },
        as_node="categorize_email",
    )

    result = graph.invoke(
        None,
        config=config,
        interrupt_after="draft_response",
    )

    assert 1 <= result["priority_score"] <= 3
