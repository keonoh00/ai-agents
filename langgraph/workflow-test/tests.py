import os

import pytest
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langgraph.graph.state import RunnableConfig
from main import graph
from pydantic import BaseModel, Field

config: RunnableConfig = {
    "configurable": {
        "thread_id": "1",
    }
}

load_dotenv(dotenv_path="../../.env")
llm = init_chat_model(
    "ollama:deepseek-r1:70b",
    base_url=os.environ.get("OLLAMA_BASE_URL"),
)


class SimilarityScoreOutput(BaseModel):
    similarity_score: int = Field(
        description="How similar is the response to the examples?",
        gt=0,
        lt=100,
    )


RESPONSE_EXAMPLES = {
    "urgent": [
        "Thank you for your urgent message. We are addressing this immediately and will respond as soon as possible.",
        "We've received your urgent request and are prioritizing it. Our team is on it right away.",
        "This urgent matter has our immediate attention. We'll respond promptly.",
    ],
    "normal": [
        "Thank you for your email. We'll review it and get back to you within 24-48 hours.",
        "We've received your message and will respond soon. Thank you for reaching out.",
        "Thank you for contacting us. We'll process your request and respond shortly.",
        "Thank you for the update. I will review the information and follow up as needed.",
        "Thank you for the update on the project status. I will review and follow up by the end of the week.",
        "Thanks for sharing this update. We'll review and respond accordingly.",
    ],
    "spam": [
        "This message has been flagged as spam and filtered.",
        "This email has been identified as promotional content.",
        "This message has been marked as spam.",
    ],
}


def judge_response(response: str, category: str):
    s_llm = llm.with_structured_output(SimilarityScoreOutput)
    examples = RESPONSE_EXAMPLES.get(category, [])
    result = s_llm.invoke(
        f"""
        Score how similar this response is to the examples.

        Category: {category}

        Examples:
        {"\n".join(examples)}

        Response to evaluate:
        {response}

        Scoring criteria:
        - 90-100: Very similar in tone, content, and intent
        - 70-89: Similar with minor differences
        - 50-69: Moderately similar, captures main idea
        - 30-49: Some similarity but missing key elements
        - 0-29: Very different or inappropriate
        """
    )
    validated = SimilarityScoreOutput.model_validate(result)
    return validated.similarity_score


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
    arb_state = {
        "category": "spam",
        "email": "Get righ quick!!! I have a pyramid scheme for you!",
        "priority_score": 1,
    }
    result = graph.nodes["draft_response"].invoke(arb_state)
    similarity_score = judge_response(
        result.get("response", ""),
        "spam",
    )
    assert similarity_score > 70


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
