import dotenv

dotenv.load_dotenv(dotenv_path="../../.env")

import asyncio

import streamlit as st
from agents import Agent, Runner, SQLiteSession

if "agent" not in st.session_state:
    st.session_state.agent = Agent(
        name="Chat GPT Clone",
        instructions="You are a helpful assistant",
    )
if "session" not in st.session_state:
    st.session_state.session = SQLiteSession(
        session_id="chat-history",
        db_path="chat-history.db",
    )

agent = st.session_state.agent
session = st.session_state.session

st.title("Chat GPT Clone")


async def run_agent(user_input):
    stream = Runner.run_streamed(agent, user_input, session=session)
    async for event in stream.stream_events():
        if event.type == "raw_response_event":
            if event.data.type == "response.output_text.delta":
                with st.chat_message("ai"):
                    st.write(event.data.delta)


user_input = st.text_input("Enter your message:")

if user_input:
    with st.chat_message("user"):
        st.write(user_input)
    asyncio.run(run_agent(user_input))

with st.sidebar:
    reset = st.button("Reset Memory")
    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))
