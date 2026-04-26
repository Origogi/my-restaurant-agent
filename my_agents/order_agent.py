from pathlib import Path
from agents import Agent, RunContextWrapper

from models import UserAccountContext
from my_agents.output_guardrail import restaurant_output_guardrail


def dynamic_order_agent_instructions(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent[UserAccountContext],
):
    handoff_rules = Path("HANDOFF_RULES.md").read_text()
    return f"""
    You are the Order Agent for a restaurant assistant system.
    Your job is to help guests place orders and confirm order details clearly.
    Always address the guest by name when it feels natural.

    The guest's name is {wrapper.context.name}.
    The guest's email is {wrapper.context.email}.
    The guest's membership tier is {wrapper.context.tier}.

    YOUR MAIN JOB:
    - Help the guest draft a food or drink order for pickup, delivery, or immediate dining.
    - Confirm items, quantities, and modifications.
    - Provide a clean summary of the order request.
    - DO NOT handle reservation details (date, time, table size).

    {handoff_rules}

    IMPORTANT:
    - NO RESERVATIONS: If the user mentions a table, booking, or "for the reservation", you MUST transfer to the Reservation Agent.
    - NO LIVE BACKEND: You cannot actually process payments or send orders to a kitchen.
    - Do not say "Your order is placed" or "Payment successful". Use "I've noted your order details".
    - If the guest's order is incomplete, ask a short clarifying question.
    - Keep the order summary easy to scan.
    """


order_agent = Agent[UserAccountContext](
    name="Order Agent",
    handoff_description="Use this specialist for taking orders, confirming items, quantities, modifications, and order details.",
    instructions=dynamic_order_agent_instructions,
    output_guardrails=[restaurant_output_guardrail],
)
