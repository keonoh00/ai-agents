import json
import os
from typing import Any, Callable, Literal, Optional, Sequence

from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Command
from pydantic import BaseModel

OLLAMA_BASE_URL: str = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.environ.get("OLLAMA_MODEL", "ollama:gpt-oss:latest")

llm = init_chat_model(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)


class AgentState(MessagesState):
    current_agent: Optional[str]
    transfered_by: Optional[str]
    reasoning: Optional[str]
    user_query: Optional[str]
    resource_map: Optional[dict[str, Any]]
    supervisor_plan: Optional[str]
    next_agent: Optional[str]  # For routing decisions


def _stringify_message_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for chunk in content:
            if isinstance(chunk, dict):
                if "text" in chunk:
                    parts.append(str(chunk["text"]))
                elif "content" in chunk:
                    parts.append(str(chunk["content"]))
            else:
                parts.append(str(chunk))
        return "\n".join(part for part in parts if part)
    return str(content)


def format_conversation_history(
    messages: Sequence[BaseMessage] | list[BaseMessage] | None,
) -> str:
    if not messages:
        return ""
    lines: list[str] = []
    for message in messages:
        role = getattr(message, "type", message.__class__.__name__)
        lines.append(f"{role.upper()}: {_stringify_message_content(message.content)}")
    return "\n".join(lines)


def get_user_query(state: AgentState) -> str:
    query = state.get("user_query")
    if query:
        return str(query)
    for message in state.get("messages", []):
        if getattr(message, "type", "") == "human":
            return _stringify_message_content(message.content)
    return ""


def render_prompt(prompt_template: str, state: AgentState) -> str:
    conversation = format_conversation_history(state.get("messages", []))
    resource_map = state.get("resource_map") or {}
    prompt_context = {
        "user_query": get_user_query(state),
        "resource_map": (
            json.dumps(resource_map, indent=2) if resource_map else "Unavailable"
        ),
        "messages": conversation or "No prior conversation.",
        "supervisor_plan": state.get("supervisor_plan")
        or state.get("reasoning")
        or "Not specified.",
    }
    return prompt_template.format(**prompt_context)


class RoutingDecision(BaseModel):
    next_agent: Literal[
        "network_manager",
        "traffic_controller",
        "tech_reporter",
        "general_chatbot",
        "__end__",
    ]
    reasoning: str


def make_agent(
    prompt: str,
    tools: list[Callable],
    agent_name: str,
):
    def agent_node(state: AgentState):
        llm_with_tools = llm.bind_tools(tools)

        # Add routing instructions to the prompt
        # Note: We use quadruple braces {{{{ to escape JSON braces in the format string
        routing_prompt = f"""{prompt}

**Routing Decision:**
After completing your response, decide where the conversation should go next:
- If you need another agent's help, route to them directly (e.g., if you found an issue, route to "traffic_controller").
- If the task is complete and the user is satisfied, route to "__end__" to end the conversation.
- If you need more information or diagnostics, route to "network_manager".
- If you need to summarize findings, route to "tech_reporter".
- For general conversation, route to "general_chatbot".

Available agents: network_manager, traffic_controller, tech_reporter, general_chatbot, __end__

At the end of your response, include a routing decision in this format:
ROUTING_DECISION: {{{{ "next_agent": "agent_name", "reasoning": "why you're routing there" }}}}
"""
        prompt_text = render_prompt(routing_prompt, state)
        response = llm_with_tools.invoke(prompt_text)

        # Try to extract routing decision from the response
        routing_decision: RoutingDecision | None = None
        response_content = _stringify_message_content(response.content)
        match = None

        # Look for routing decision in the response
        if "ROUTING_DECISION:" in response_content:
            try:
                import re

                match = re.search(
                    r"ROUTING_DECISION:\s*(\{.*?\})", response_content, re.DOTALL
                )
                if match:
                    routing_json = match.group(1)
                    routing_decision = RoutingDecision.model_validate_json(routing_json)
            except Exception:
                pass

        # If no routing decision found, use LLM to extract it
        if routing_decision is None:
            structured_llm = llm.with_structured_output(RoutingDecision)
            routing_extraction_prompt = f"""Based on this agent's response, determine where the conversation should go next:

Agent Response: {response_content}
Conversation History: {format_conversation_history(state.get("messages", []))}

Decide the next agent or end the conversation."""
            try:
                result = structured_llm.invoke(routing_extraction_prompt)
                if isinstance(result, dict):
                    routing_decision = RoutingDecision.model_validate(result)
                elif isinstance(result, RoutingDecision):
                    routing_decision = result
                else:
                    routing_decision = RoutingDecision.model_validate(result)
            except Exception:
                # Default to ending if we can't determine routing
                routing_decision = RoutingDecision(
                    next_agent="__end__", reasoning="Unable to determine next step"
                )

        # At this point, routing_decision is guaranteed to be a RoutingDecision
        if not isinstance(routing_decision, RoutingDecision):
            routing_decision = RoutingDecision(
                next_agent="__end__", reasoning="Invalid routing decision"
            )

        # Clean the response content to remove routing decision marker
        cleaned_content = response_content
        if match:
            cleaned_content = cleaned_content.replace(match.group(0), "").strip()
        elif "ROUTING_DECISION:" in cleaned_content:
            # Remove the marker even if regex didn't match
            lines = cleaned_content.split("\n")
            cleaned_lines = []
            skip_next = False
            for line in lines:
                if "ROUTING_DECISION:" in line:
                    skip_next = True
                    continue
                if skip_next and line.strip().startswith("{"):
                    continue
                skip_next = False
                cleaned_lines.append(line)
            cleaned_content = "\n".join(cleaned_lines).strip()

        # Create a new response with cleaned content
        if hasattr(response, "content") and isinstance(response.content, str):
            response.content = cleaned_content
        elif hasattr(response, "content") and isinstance(response.content, list):
            # If content is a list, update it
            for chunk in response.content:
                if isinstance(chunk, dict) and "text" in chunk:
                    chunk["text"] = cleaned_content
                    break

        # Store routing decision in state
        next_agent_value = (
            routing_decision.next_agent
            if routing_decision.next_agent != "__end__"
            else None
        )
        return {
            "messages": [response],
            "current_agent": agent_name,
            "reasoning": routing_decision.reasoning,
            "next_agent": next_agent_value,
        }

    agent_builder = StateGraph(AgentState)

    agent_builder.add_node("agent", agent_node)
    agent_builder.add_node(
        "tools",
        ToolNode(tools=tools),
    )

    agent_builder.add_edge(START, "agent")
    agent_builder.add_conditional_edges("agent", tools_condition)
    agent_builder.add_edge("tools", "agent")
    # Agent subgraph always ends - main workflow handles routing
    agent_builder.add_edge("agent", END)
    return agent_builder.compile()
