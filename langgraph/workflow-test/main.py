import os
from typing import Literal, NotRequired

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

load_dotenv(dotenv_path="../../.env")
llm = init_chat_model(
    "ollama:deepseek-r1:70b",
    base_url=os.environ.get("OLLAMA_BASE_URL"),
)
checkpointer = MemorySaver()


class EmailState(TypedDict):
    email: NotRequired[str]
    category: NotRequired[Literal["spam", "normal", "urgent"]]
    priority_score: NotRequired[int]
    response: NotRequired[str]


class EmailClassificationResponse(BaseModel):
    category: Literal["spam", "normal", "urgent"] = Field(
        description="Category of the email"
    )


class PriorityScoreResponse(BaseModel):
    priority_score: int = Field(
        description="Priority score from 1 to 10",
        ge=1,
        le=10,
    )


def categorize_email(state: EmailState) -> EmailState:
    struct_llm = llm.with_structured_output(EmailClassificationResponse)
    result = struct_llm.invoke(
        f"""
        Classify this email into one of three categories:
        - urgent: time-sensitive, requires immediate attention
        - normal: regular business communication
        - spam: promotional, marketing, or unwanted content

        Email: {state.get("email", "")}
        """
    )
    validated = EmailClassificationResponse.model_validate(result)
    return {
        "category": validated.category,
    }


def assign_priority(state: EmailState) -> EmailState:
    s_llm = llm.with_structured_output(PriorityScoreResponse)

    result = s_llm.invoke(
        f"""Assign a priority score from 1-10 for this {state.get("category","")} email.
        Consider:
        - Category: {state.get("category","")}
        - Email content: {state.get("email","")}

        Guidelines:
        - Urgent emails: usually 8-10
        - Normal emails: usually 4-7
        - Spam emails: usually 1-3"""
    )

    validated = PriorityScoreResponse.model_validate(result)

    return {"priority_score": validated.priority_score}


def draft_response(state: EmailState) -> EmailState:
    email = state.get("email", "")
    category = state.get("category", "normal")
    priority_score = state.get("priority_score", "")
    result = llm.invoke(
        f"""Draft a brief, professional response for this {category} email.

        Original email: {email}
        Category: {category}
        Priority: {priority_score}/10

        Guidelines:
        - Urgent: Acknowledge urgency, promise immediate attention
        - Normal: Professional acknowledgment, standard timeline
        - Spam: Brief notice that message was filtered

        Keep response under 2 sentences."""
    )
    validated = BaseMessage.model_validate(result)
    return {
        "response": validated.content,
    }


graph_builder = StateGraph(EmailState)

graph_builder.add_node("categorize_email", categorize_email)
graph_builder.add_node("assign_priority", assign_priority)
graph_builder.add_node("draft_response", draft_response)

graph_builder.add_edge(START, "categorize_email")
graph_builder.add_edge("categorize_email", "assign_priority")
graph_builder.add_edge("assign_priority", "draft_response")
graph_builder.add_edge("draft_response", END)

graph = graph_builder.compile(checkpointer=checkpointer)
