import pytest
from main import graph


@pytest.mark.parametrize(
    "email, expected_category, expected_score",
    [
        ("this is urgent", "urgent", 10),
        ("I wanna talk to you", "normal", 5),
        ("I have an offer", "spam", 1),
    ],
)
def test_full_graph(email, expected_category, expected_score):
    result = graph.invoke(
        {
            "email": email,
        }
    )

    assert result["category"] == expected_category
    assert result["priority_score"] == expected_score
