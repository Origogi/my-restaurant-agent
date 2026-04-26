import dotenv

from openai import OpenAI
import asyncio
import json
import streamlit as st
from agents import (
    InputGuardrailTripwireTriggered,
    OutputGuardrailTripwireTriggered,
    Runner,
    SQLiteSession,
)
from models import UserAccountContext
from my_agents import triage_agent

dotenv.load_dotenv()


client = OpenAI()

user_account_ctx = UserAccountContext(
    customer_id=1,
    name="Origogi",
    email="origogi@example.com",
    tier="basic",
)


if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "chat-history",
        "customer-support-memory.db",
    )
session = st.session_state["session"]

if "handoff_logs" not in st.session_state:
    st.session_state["handoff_logs"] = []


async def paint_history():
    messages = await session.get_items()
    for message in messages:
        if "role" in message:
            # Determine label based on role and metadata
            label = "human" if message["role"] == "user" else "ai"
            if label == "ai" and "sender" in message:
                label = f"ai ({message['sender']})"

            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.write(message["content"])
                else:
                    if message["type"] == "message":
                        st.write(message["content"][0]["text"].replace("$", "\\$"))
        elif (
            message.get("type") == "function_call"
            and message.get("name", "").startswith("transfer_to_")
        ):

            handoff_data = json.loads(message["arguments"])
            with st.chat_message("ai"):
                st.write(f"🤖 Transferred to {handoff_data['to_agent_name']}")


asyncio.run(paint_history())


if "current_agent" not in st.session_state:
    st.session_state["current_agent"] = triage_agent

async def run_agent(message):
    current_agent_name = st.session_state["current_agent"].name
    with st.chat_message("ai"):
        st.caption(f"Connected to: **{current_agent_name}**")
        handoff_placeholder = st.empty()
        text_placeholder = st.empty()
        response = ""

        st.session_state["handoff_placeholder"] = handoff_placeholder
        st.session_state["text_placeholder"] = text_placeholder

        try:
            initial_agent_name = st.session_state["current_agent"].name
            stream = Runner.run_streamed(
                st.session_state["current_agent"],
                message,
                session=session,
                context=user_account_ctx,
            )

            async for event in stream.stream_events():
                if event.type == "agent_updated_stream_event":
                    new_agent = event.new_agent
                    # Only show transfer message if it's a specialist (skip Triage in UI)
                    if new_agent.name != initial_agent_name:
                        if new_agent.name != "Triage Agent":
                            handoff_placeholder.write(f"🤖 Transferred to {new_agent.name}")
                            text_placeholder.empty()
                            text_placeholder = st.empty()
                            st.session_state["text_placeholder"] = text_placeholder
                            response = ""
                        current_agent_name = new_agent.name
                        st.caption(f"Connected to: **{current_agent_name}**")
                        initial_agent_name = new_agent.name
                    
                    st.session_state["current_agent"] = new_agent

                elif event.type == "raw_response_event":

                    if event.data.type == "response.output_text.delta":
                        response += event.data.delta
                        text_placeholder.write(response.replace("$", "\\$"))
        except InputGuardrailTripwireTriggered as exc:
            handoff_placeholder.empty()
            output_info = exc.guardrail_result.output.output_info
            reason = getattr(
                output_info,
                "reason",
                "I can only help with restaurant-related requests.",
            )
            text_placeholder.write(reason.replace("$", "\\$"))
        except OutputGuardrailTripwireTriggered as exc:
            handoff_placeholder.empty()
            output_info = exc.guardrail_result.output.output_info
            reason = getattr(
                output_info,
                "reason",
                "I cannot provide that response safely in this restaurant workflow.",
            )
            text_placeholder.write(reason.replace("$", "\\$"))


message = st.chat_input(
    "레스토랑 예약, 메뉴 문의 및 관리 관련 내용을 입력해 주세요.",
)

if message:
    if "text_placeholder" in st.session_state:
        st.session_state["text_placeholder"].empty()

    if message:
        with st.chat_message("human"):
            st.write(message)
        asyncio.run(run_agent(message))


with st.sidebar:
    st.info(f"🟢 **Current Agent:** {st.session_state['current_agent'].name}")
    
    reset = st.button("Reset memory")
    if reset:
        asyncio.run(session.clear_session())
        st.session_state["handoff_logs"] = []

    st.subheader("Session")
    st.write(asyncio.run(session.get_items()))
