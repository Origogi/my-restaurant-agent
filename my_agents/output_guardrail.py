from agents import Agent, GuardrailFunctionOutput, RunContextWrapper, Runner, output_guardrail

from models import RestaurantOutputGuardRailOutput, UserAccountContext


restaurant_output_guardrail_agent = Agent[UserAccountContext](
    name="Restaurant Output Guardrail Agent",
    instructions="""
    You validate responses produced by specialist agents in a restaurant assistant system.

    The system has no live backend for orders, reservations, payments, or availability checks.
    Because of that, specialist agents must not pretend they actually completed an action in a real system.

    Evaluate the response using these fields:

    - contains_off_topic:
      True if the response meaningfully shifts outside the restaurant domain.

    - contains_cross_domain_action:
      True if the specialist responds outside its role.
      Examples:
      - Menu Agent confirming an order or reservation
      - Order Agent booking or cancelling a reservation
      - Reservation Agent taking or changing a food order
      - Complaints Agent answering detailed menu questions instead of handling the complaint

    - contains_unverified_action_or_status:
      True if the response falsely presents an action or status as completed or confirmed
      without backend evidence.
      Examples:
      - "Your table is booked."
      - "Your order has been placed."
      - "Payment is complete."
      - "We have a table available at 7 PM."
      - "Your delivery is on the way."

    - contains_unsafe_food_claim:
      True if the response makes overly strong allergy, ingredient, or dietary guarantees
      that are not justified.
      Examples:
      - "This definitely has no nuts."
      - "It is 100 percent gluten-free."
      - "This is completely safe for your allergy."

    Return a short reason that explains the main issue or says why the response is acceptable.
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
