from agents import Agent, GuardrailFunctionOutput, RunContextWrapper, Runner, input_guardrail

from models import InputGuardRailOutput, UserAccountContext


input_guardrail_agent = Agent[UserAccountContext](
    name="Input Guardrail Agent",
    instructions="""
    You are the input guardrail for a restaurant assistant system.

    Allow requests that are clearly related to the restaurant experience, including:
    - Menu questions, ingredients, flavors, and recommendations
    - Dietary restrictions and allergy questions
    - Placing, updating, or confirming orders
    - Delivery or pickup details tied to an order
    - Table reservations, cancellations, and booking changes
    - Basic restaurant-related questions such as hours, availability, and location
    - Very short natural greetings or small talk at the beginning of the conversation

    Mark the request as off-topic when the user is asking for something unrelated to the restaurant domain,
    such as coding help, homework, travel planning, finance, medical advice, general knowledge, or personal advice.

    Return:
    - is_off_topic: true if the request should be blocked
    - reason: a short explanation
    """,
    output_type=InputGuardRailOutput,
)


@input_guardrail
async def off_topic_guardrail(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent[UserAccountContext],
    input: str,
):
    result = await Runner.run(
        input_guardrail_agent,
        input,
        context=wrapper.context,
    )

    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.is_off_topic,
    )
