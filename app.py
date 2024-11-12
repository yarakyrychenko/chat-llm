import streamlit as st
from openai import OpenAI
from datetime import datetime

if 'inserted' not in st.session_state:
    st.session_state.inserted = 0

system_string = """You are an expert at explaining and motivating climate action. Try to find a way the user can engage in climate action and motivate them. Respond in line with the following principles:

1. When evidencing the reality and urgency of climate change:
   - Highlight the high degree of scientific consensus on human-caused climate change.
   - Avoid endorsing misinformation and minimize inaccurate information on climate change.
   - Focus on impacts of climate change that are timely and local to the user.

3. When discussing climate change with someone concerned about the issue:
   - Emphasize potential solutions and individual and collective actions to reduce climate change.
   - Highlight that many people, organizations, and leaders share the user's concerns, reducing isolation and enhancing support.
  - Emphasize that collective and political actions can drive significant societal changes while encouraging individual/household efforts.
   - Highlight the feasibility of engaging in climate action.

4. When discussing solutions to climate change:
   - Prioritize high-impact behaviors (e.g., reducing air travel) over low-impact actions (e.g., recycling).
   - Showcase public efforts and foster a sense of collective efficacy, reinforcing social norms around climate action.
   - Frame climate policies in terms of potential gains rather than losses.

Respond with at most 100 words. Use bullet points and follow up questions when necessary. Provide specific information and avoid general statements."""

def setup_messages():
    if 'cnd' in st.query_params:
        if st.query_params["cnd"] == "clm":
            st.session_state.messages = [{ "role": "system", "content": st.session_state.system_message if 'system_message' in st.session_state else system_string}]
        else:
            st.session_state.messages = []
    else:
        st.session_state.messages = []

st.title("Chat with me!")
st.write(f"You have submitted {st.session_state.inserted} conversation(s).")
st.text_area(
    "System message (Ignored in Control Condition)",
    system_string, key='system_message',on_change=setup_messages)

left, right = st.columns(2)

with left:
    with st.expander("ℹ️ Information"):
        st.caption(
        """👉 Chat with a language model by typing in the chat box. 
        👉 When you are done with a conversation, submit it using the End Conversation tab. 
        👉 You can only type up to ten messages per conversation and the model might be unavialble at times due to high demand.
        """
        )

with right:
    with st.expander("⏹️ End Conversation"):
        st.text_input(label="Enter your Prolific ID",key="user_id")
        st.slider('Rate the conversation from *Terrible* to *Perfect*. There are no right or wrong answers.', 0, 100, format="", key="score", value=50)
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

                    setup_messages()
                    st.rerun()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o-mini-2024-07-18"

if "messages" not in st.session_state:
    setup_messages()

if "max_messages" not in st.session_state:
    st.session_state.max_messages = 20

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
        
