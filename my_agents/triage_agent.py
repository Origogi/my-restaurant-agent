import streamlit as st
from agents import Agent, RunContextWrapper, handoff

from models import HandoffData, UserAccountContext
from my_agents.complaints_agent import complaints_agent
from my_agents.input_guardrail import off_topic_guardrail
from my_agents.menu_agent import menu_agent
from my_agents.order_agent import order_agent
from my_agents.reservation_agent import reservation_agent


def handle_handoff(
    wrapper: RunContextWrapper[UserAccountContext],
    input_data: HandoffData,
):
    handoff_logs = st.session_state.setdefault("handoff_logs", [])
    handoff_logs.append(input_data.model_dump())


def make_handoff(agent: Agent[UserAccountContext], issue_type: str):
    def on_handoff(
        wrapper: RunContextWrapper[UserAccountContext],
        input_data: HandoffData,
    ):
        handle_handoff(
            wrapper,
            input_data.model_copy(
                update={
                    "to_agent_name": agent.name,
                    "issue_type": issue_type,
                }
            ),
        )

    return handoff(
        agent=agent,
        on_handoff=on_handoff,
        input_type=HandoffData,
        tool_name_override=f"transfer_to_{issue_type}_agent",
    )


def dynamic_triage_agent_instructions(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent[UserAccountContext],
):
    return f"""
    You are the Triage Agent for a restaurant assistant system.
    
    YOUR ROLES:
    1. FRIENDLY GREETER: For simple greetings (hello, hi, how are you), be warm and professional. 
       Always address the guest by name: {wrapper.context.name}.
    2. SILENT ROUTER: As soon as a specific request is detected (menu, order, reservation, complaint), 
       IMMEDIATELY call the correct transfer tool and STOP talking. Do not explain the transfer.

    ROUTING RULES:
    - Menu Agent: menu items, ingredients, recommendations, dietary info.
    - Order Agent: placing orders, checking/modifying order details.
    - Reservation Agent: booking, changing, or canceling table reservations.
    - Complaints Agent: negative experiences, manager requests, refunds.

    IMPORTANT:
    - If you are calling a tool, your text response MUST be empty or extremely brief.
    - If the user is just saying hello, ask how you can help them today.
    """



triage_agent = Agent[UserAccountContext](
    name="Triage Agent",
    instructions=dynamic_triage_agent_instructions,
    input_guardrails=[off_topic_guardrail],
    handoffs=[
        make_handoff(menu_agent, "menu"),
        make_handoff(order_agent, "order"),
        make_handoff(reservation_agent, "reservation"),
        make_handoff(complaints_agent, "complaint"),
    ],
)

# Hub-and-Spoke + Direct Specialist Handoffs: 
# Inject handoffs to avoid circular imports and enable direct transfers
specialists = [menu_agent, order_agent, reservation_agent, complaints_agent]
all_agents = specialists + [triage_agent]

for source_agent in specialists:
    if source_agent.handoffs is None:
        source_agent.handoffs = []
    
    for target_agent in all_agents:
        if source_agent.name != target_agent.name:
            # Determine issue type for the tool name
            issue_type = target_agent.name.lower().replace(" agent", "")
            source_agent.handoffs.append(make_handoff(target_agent, issue_type))

