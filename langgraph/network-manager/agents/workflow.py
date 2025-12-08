from agents.common import AgentState
from agents.general_chatbot.agent import general_chatbot
from agents.network_manager.agent import network_manager
from agents.tech_reporter.agent import tech_reporter
from agents.traffic_controller.agent import traffic_controller
from langgraph.graph import END, START, StateGraph


def route_to_next_agent(state: AgentState):
    """Route to the next agent based on the routing decision, or end the conversation"""
    next_agent = state.get("next_agent")
    if next_agent is None:
        return END
    return str(next_agent)


workflow = StateGraph(AgentState)

# Add all agent nodes
workflow.add_node("network_manager", network_manager)
workflow.add_node("traffic_controller", traffic_controller)
workflow.add_node("tech_reporter", tech_reporter)
workflow.add_node("general_chatbot", general_chatbot)

# Start with general_chatbot by default (can be changed based on initial routing logic)
workflow.add_edge(START, "general_chatbot")

# Add conditional edges from each agent to route to the next agent or end
workflow.add_conditional_edges("network_manager", route_to_next_agent)
workflow.add_conditional_edges("traffic_controller", route_to_next_agent)
workflow.add_conditional_edges("tech_reporter", route_to_next_agent)
workflow.add_conditional_edges("general_chatbot", route_to_next_agent)

graph = workflow.compile()
