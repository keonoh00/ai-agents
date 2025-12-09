import os
from typing import Callable, Literal

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Command
from pydantic import BaseModel


class SupervisorOutput(BaseModel):
    next_agent: Literal["korean_agent", "spanish_agent", "greek_agent"]
    reasoning: str


class AgentsState(MessagesState):
    current_agent: str
    transfered_by: str


load_dotenv(dotenv_path="../../.env")
llm = init_chat_model(
    "openai:gpt-4o-mini",
    # base_url=os.environ.get("OLLAMA_BASE_URL"),
)


def make_agent(prompt: str, tools: list[Callable]):
    def agent_node(state: AgentsState):
        llm_with_tools = llm.bind_tools(tools)
        response = llm_with_tools.invoke(
            f"""
            {prompt}

            Conversation History:
            {state["messages"]}
            """
        )

        return {
            "messages": [response],
        }

    agent_builder = StateGraph(AgentsState)

    agent_builder.add_node("agent", agent_node)
    agent_builder.add_node(
        "tools",
        ToolNode(tools=tools),
    )

    agent_builder.add_edge(START, "agent")
    agent_builder.add_conditional_edges("agent", tools_condition)
    agent_builder.add_edge("tools", "agent")
    agent_builder.add_edge("agent", END)
    return agent_builder.compile()


def supervisor(state: AgentsState):
    structured_llm = llm.with_structured_output(SupervisorOutput)
    print(state["messages"])
    response = structured_llm.invoke(
        f"""
            You are a supervisor that routes conversations to the appropriate language agent.

            Analyse the customers request and the conversation history and decide which agent should handle the conversation.

            The options for the next agent are:
            - greek_agent
            - spanish_agent
            - korean_agent 
            
            <CONVERSATION_HISTORY>
            {state.get("messages", [])}
            </CONVERSATION_HISTORY>

            IMPORTANT:
            
            
            Never transfer to the same agent twice in a row.

            If the agent has replied feel free to end the conversation by returning __end__
        """
    )
    validated_response = SupervisorOutput.model_validate(response)
    return Command(
        goto=validated_response.next_agent,
        update={
            "reasoning": validated_response.reasoning,
        },
    )


graph_builder = StateGraph(AgentsState)
graph_builder.add_node(
    "supervisor",
    supervisor,
    destinations=("korean_agent", "greek_agent", "spanish_agent"),
)
graph_builder.add_node(
    "korean_agent",
    make_agent(
        prompt="You're a Korean customer support agent. You only speak and understand Korean.",
        tools=[],
    ),
)
graph_builder.add_node(
    "greek_agent",
    make_agent(
        prompt="You're a Greek customer support agent. You only speak and understand Greek.",
        tools=[],
    ),
)
graph_builder.add_node(
    "spanish_agent",
    make_agent(
        prompt="You're a Spanish customer support agent. You only speak and understand Spanish.",
        tools=[],
    ),
)

graph_builder.add_edge(START, "supervisor")
graph_builder.add_edge("korean_agent", "supervisor")
graph_builder.add_edge("greek_agent", "supervisor")
graph_builder.add_edge("spanish_agent", "supervisor")

graph = graph_builder.compile()
