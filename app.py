import streamlit as st
from openai import OpenAI

st.title("Chat LLM")
with st.expander("ℹ️ Disclaimer"):
    st.caption(
        """This demo is designed to
        process a maximum of 10 interactions and may be unavailable if too many
        people use the service concurrently. Thank you for your understanding.
        """
    )

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
system_message = "You are a helpful assistant."

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

if "messages" not in st.session_state:
    if 'cnd' in st.query_params:
        if st.query_params["cnd"] == "clm":
            st.session_state.messages = [{ "role": "system", "content": system_message }]
            st.write(system_message)
        else:
            st.session_state.messages = []
    else:
        st.session_state.messages = []

if "max_messages" not in st.session_state:
    # Counting both user and assistant messages, so 10 rounds of conversation
    st.session_state.max_messages = 20

with st.container(border=True):
    st.session_state.user_id = st.text_input(label="Enter your Prolific ID")
    if st.button('End Conversation', key=None, help=None, type="secondary", icon=None, disabled=False, use_container_width=False):
        user_data={"user_id":st.session_state.user_id,"conversation":st.session_state.messages}
        from pymongo.mongo_client import MongoClient
        from pymongo.server_api import ServerApi
        with MongoClient(st.secrets["mongo"],server_api=ServerApi('1')) as client:
                    db = client.mist
                    collection = db.app
                    collection.insert_one(user_data)  
                    st.session_state.inserted = True


for message in st.session_state.messages:
    if message['role']!='system':
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if len(st.session_state.messages) >= st.session_state.max_messages:
    st.info(
        """Notice: The maximum message limit for this demo version has been reached. Thank you for your understanding."""
    )

else:
    if prompt := st.chat_input("What is up?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            try:
                stream = client.chat.completions.create(
                    model=st.session_state["openai_model"],
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                    stream=True,
                )
                response = st.write_stream(stream)
                st.session_state.messages.append(
                    {"role": "assistant", "content": response}
                )
            except:
                st.session_state.max_messages = len(st.session_state.messages)
                rate_limit_message = """
                    Oops! Sorry, I can't talk now. Too many people have used
                    this service recently.
                """
                st.session_state.messages.append(
                    {"role": "assistant", "content": rate_limit_message}
                )
                st.rerun()


