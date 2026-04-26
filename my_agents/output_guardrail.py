from agents import Agent, GuardrailFunctionOutput, RunContextWrapper, Runner, output_guardrail

from models import RestaurantOutputGuardRailOutput, UserAccountContext


restaurant_output_guardrail_agent = Agent[UserAccountContext](
    name="Restaurant Output Guardrail Agent",
    instructions="""
    You validate responses produced by specialist agents in a restaurant assistant system.
    This is a prototype/simulation, so agents are expected to be helpful and proactive.

    Evaluate the response using these fields:

    - contains_off_topic:
      True ONLY if the response shifts completely outside the restaurant domain (e.g., talking about politics, coding, or unrelated industries).

    - contains_cross_domain_action:
      True ONLY if a specialist tries to COMPLETELY take over another agent's primary function in a confusing way.
      ACCEPTABLE: Small helpful gestures like a Menu Agent saying "I'll make a note for your reservation" or an Order Agent saying "I'll let the staff know about your complaint" are OK for a natural flow.
      BLOCK ONLY IF: The Menu Agent tries to fully manage a reservation (e.g., "I have cancelled your table for 4 at 7 PM and booked a new one for 8 PM").

    - contains_unverified_action_or_status:
      True ONLY if the agent makes a legally or financially sensitive guarantee that is clearly impossible or dangerous.
      Helpful phrases like "I will proceed with your reservation", "I've noted your order", or "I will check that for you" are ACCEPTABLE and encouraged for a good user experience in this simulation.
      Only block if it says something like "I have already charged your credit card $500" or "I have legally transferred ownership of this restaurant to you".

    - contains_unsafe_food_claim:
      True if the response makes 100% absolute guarantees about life-threatening allergies without any caution.
      Example: "This dish is 100% guaranteed nut-free and you will have zero reaction."
    
    Return a short reason that explains your decision. Be permissive and lean towards 'False' for triggered flags unless there is a clear violation.
    """,
    output_type=RestaurantOutputGuardRailOutput,
)


@output_guardrail
async def restaurant_output_guardrail(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent[UserAccountContext],
    output: str,
):
    review_prompt = f"""
    Active specialist agent: {agent.name}

    Apply the role rules below.

    Menu Agent is allowed to discuss menu items, ingredients, flavors, recommendations,
    and dietary considerations. It must not confirm real orders or reservations.

    Order Agent is allowed to help draft, modify, and summarize an order request.
    It must not claim the order, payment, refund, delivery, or tracking status is actually confirmed.

    Reservation Agent is allowed to help gather and summarize reservation details.
    It must not claim a reservation or table availability is actually confirmed in a live system.

    Complaints Agent is allowed to acknowledge complaints, apologize, offer resolution options
    such as refund review, future discount, voucher, or manager callback, and recommend escalation
    for serious incidents. It must not claim the refund, callback, investigation, or compensation
    has already been completed unless it is actually confirmed by a live system.

    Response to validate:
    {output}
    """

    result = await Runner.run(
        restaurant_output_guardrail_agent,
        review_prompt,
        context=wrapper.context,
    )

    validation = result.final_output
    triggered = (
        validation.contains_off_topic
        or validation.contains_cross_domain_action
        or validation.contains_unverified_action_or_status
        or validation.contains_unsafe_food_claim
    )

    return GuardrailFunctionOutput(
        output_info=validation,
        tripwire_triggered=triggered,
    )
