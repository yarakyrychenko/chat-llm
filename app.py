import streamlit as st
from openai import OpenAI
from datetime import datetime

if 'inserted' not in st.session_state:
    st.session_state.inserted = 0


st.title("Chat LLM")
st.write(f"You have submitted {st.session_state.inserted} conversations.")
system_message = st.text_area(
    "System message (Ignored in Control Condition)",
      "You are an assistant knowlageable in climate change and what actions an individual should take to help address it.")

def setup_messages(system_message):
    if 'cnd' in st.query_params:
        if st.query_params["cnd"] == "clm":
            st.session_state.messages = [{ "role": "system", "content": system_message }]
        else:
            st.session_state.messages = []
    else:
        st.session_state.messages = []

left, right = st.columns(2)

with st.expander("ℹ️ Disclaimer"):
    st.caption(
    """This app may be unavailable if too many people are using it currently. You can only submit up to ten messages per conversation. Thank you for your understanding.
    """
    )
#with left:
if False:
    with st.expander("ℹ️ Disclaimer"):
        st.caption(
        """This demo is designed to
        process a maximum of 10 interactions and may be unavailable if too many
        people use the service concurrently. Thank you for your understanding.
        """
        )

if False:
    with right:
        with st.expander("End Conversation"):
            st.session_state.user_id = st.text_input(label="Enter your Prolific ID")
            if st.button('Submit', key=None, help=None):
                submission_time = datetime.now().strftime('%Y%m-%d%H-%M%S')

                user_data={"user_id":st.session_state.user_id,
                        "conversation":st.session_state.messages,
                        "time":submission_time}
                
                from pymongo.mongo_client import MongoClient
                from pymongo.server_api import ServerApi
                with MongoClient(st.secrets["mongo"],server_api=ServerApi('1')) as client:
                        db = client.chat
                        collection = db.app
                        collection.insert_one(user_data)  
                        st.session_state.inserted += 1

                        setup_messages(system_message)
                        st.rerun()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-3.5-turbo"

if "messages" not in st.session_state:
    setup_messages(system_message)

if "max_messages" not in st.session_state:
    st.session_state.max_messages = 20

with st.container():
    for message in st.session_state.messages:
        if message['role']!='system':
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    if len(st.session_state.messages) >= st.session_state.max_messages:
        st.info(
            """Notice: The maximum message limit for this demo version has been reached. Thank you for your understanding."""
        )

    else:

        if prompt := st.chat_input("Ask something..."):
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

with st.expander("End Conversation?"):
    st.text_input(label="Enter your Prolific ID",key="user_id")
    st.slider('Rate the conversation from Terrible to Perfect. There are no right or wrong answers. Use your subjective judgement', 0, 100, format="", key="score", value=50)
    if st.button('Submit', key=None, help=None):
        submission_time = datetime.now().strftime('%Y%m-%d%H-%M%S')

        user_data={"user_id":st.session_state.user_id,
                    "conversation":st.session_state.messages,
                    "score":st.session_state.score,
                    "time":submission_time}
        
        from pymongo.mongo_client import MongoClient
        from pymongo.server_api import ServerApi
        with MongoClient(st.secrets["mongo"],server_api=ServerApi('1')) as client:
                db = client.chat
                collection = db.app
                collection.insert_one(user_data)  
                st.session_state.inserted += 1

                setup_messages(system_message)
                st.rerun()
        
