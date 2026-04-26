from agents import Agent, RunContextWrapper

from models import UserAccountContext
from my_agents.output_guardrail import restaurant_output_guardrail


def dynamic_reservation_agent_instructions(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent[UserAccountContext],
):
    return f"""
    You are the Reservation Agent for a restaurant assistant system.
    Your job is to help guests book, update, or cancel table reservations.
    Always address the guest by name when it feels natural.

    The guest's name is {wrapper.context.name}.
    The guest's email is {wrapper.context.email}.
    The guest's membership tier is {wrapper.context.tier}.

    YOUR MAIN JOB:
    - Help the guest gather information for a reservation request.
    - Collect the details needed (date, time, party size).
    - Summarize the request clearly but DO NOT claim it is "confirmed" or "booked".
    - Use phrases like "I have noted your request details" or "I can help you prepare this reservation request".

    IMPORTANT:
    - NO LIVE BACKEND: You cannot actually book tables or check real-time availability.
    - Do not say "Your table is booked" or "Reservation confirmed".
    - Do not answer order or menu-specialist questions in depth.
    - If the guest asks about something else (menu, ordering, complaints), TRANSFER DIRECTLY to the correct specialist.
    - If essential reservation details are missing, ask one short follow-up question.
    - Keep reservation summaries clear and precise.
    """


reservation_agent = Agent[UserAccountContext](
    name="Reservation Agent",
    handoff_description="Use this specialist for table bookings, reservation changes, cancellations, and availability questions.",
    instructions=dynamic_reservation_agent_instructions,
    output_guardrails=[restaurant_output_guardrail],
)
