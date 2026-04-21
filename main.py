import dotenv

from openai import OpenAI
import asyncio
import json
import streamlit as st
from agents import Runner, SQLiteSession
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


async def run_agent(message):

    with st.chat_message("ai"):
        handoff_placeholder = st.empty()
        text_placeholder = st.empty()
        response = ""

        st.session_state["handoff_placeholder"] = handoff_placeholder
        st.session_state["text_placeholder"] = text_placeholder

        stream = Runner.run_streamed(
            triage_agent,
            message,
            session=session,
            context=user_account_ctx,
        )

        async for event in stream.stream_events():
            if event.type == "agent_updated_stream_event":
                if event.new_agent.name != triage_agent.name:
                    handoff_placeholder.write(f"🤖 Transferred to {event.new_agent.name}")
                    text_placeholder.empty()
                    text_placeholder = st.empty()
                    st.session_state["text_placeholder"] = text_placeholder
                    response = ""

            elif event.type == "raw_response_event":

                if event.data.type == "response.output_text.delta":
                    response += event.data.delta
                    text_placeholder.write(response.replace("$", "\\$"))


message = st.chat_input(
    "Ask about the restaurant",
)

if message:
    if "text_placeholder" in st.session_state:
        st.session_state["text_placeholder"].empty()

    if message:
        with st.chat_message("human"):
            st.write(message)
        asyncio.run(run_agent(message))


with st.sidebar:
    reset = st.button("Reset memory")
    if reset:
        asyncio.run(session.clear_session())
        st.session_state["handoff_logs"] = []

    st.subheader("Session")
    st.write(asyncio.run(session.get_items()))
