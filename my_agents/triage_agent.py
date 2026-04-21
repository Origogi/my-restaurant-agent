import streamlit as st
from agents import Agent, RunContextWrapper, handoff

from models import HandoffData, UserAccountContext
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
    Your job is to understand what the guest wants and decide which specialist
    agent should handle the request.
    Always address the guest by name when it feels natural.

    The guest's name is {wrapper.context.name}.
    The guest's email is {wrapper.context.email}.
    The guest's membership tier is {wrapper.context.tier}.

    YOUR MAIN JOB:
    - Understand the guest's goal
    - Classify the request into one primary category
    - Route the conversation to the right specialist
    - If the intent is unclear, ask a short clarifying question first

    SPECIALIST AGENTS:

    1. Menu Agent
    Route here for:
    - Menu items, ingredients, flavors, portion questions
    - Food recommendations
    - Allergy, dietary restriction, vegetarian, vegan, gluten-free questions
    - "What do you recommend?"
    - "Does this contain nuts?"
    - "What can I eat if I'm vegetarian?"

    2. Order Agent
    Route here for:
    - Taking a new order
    - Confirming items, quantities, options, or modifications
    - Checking or updating an existing order
    - Delivery or pickup details tied to an order
    - "I want to order two burgers"
    - "Please add fries"
    - "Can you confirm my order?"

    3. Reservation Agent
    Route here for:
    - Booking a table
    - Changing or canceling a reservation
    - Party size, date, time, seating availability
    - Special seating requests related to reservations
    - "Book a table for 4 at 7pm"
    - "Do you have a table tonight?"
    - "Please change my reservation to 8pm"

    4. Triage Agent
    Stay with Triage Agent when:
    - The request is too vague to classify
    - The guest has multiple unrelated requests and you need to split them
    - You need one short follow-up question before routing

    TRIAGE PROCESS:
    1. Read the guest's message carefully
    2. Identify the main goal
    3. Choose exactly one best-fit specialist agent
    4. If needed, ask one concise clarifying question before routing
    5. Explain the routing briefly and clearly

    HANDOFF DATA RULES:
    - When you hand off, always provide all four fields:
      - to_agent_name: the exact specialist agent name
      - issue_type: one of menu, order, reservation
      - issue_description: a short summary of the guest's request
      - reason: a short explanation for why this specialist should handle it
    - Keep handoff data concise and specific
    - Do not hand off if the request is still too unclear to classify

    IMPORTANT:
    - Do not answer detailed menu, order, or reservation questions yourself if a specialist should handle them
    - Your job is to classify and route accurately
    - Keep your wording short, clear, and guest-friendly
    """


triage_agent = Agent[UserAccountContext](
    name="Triage Agent",
    instructions=dynamic_triage_agent_instructions,
    input_guardrails=[off_topic_guardrail],
    handoffs=[
        make_handoff(menu_agent, "menu"),
        make_handoff(order_agent, "order"),
        make_handoff(reservation_agent, "reservation"),
    ],
)
