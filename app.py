import streamlit as st
from openai import OpenAI
from datetime import datetime

st.set_page_config(
    page_title="Chat with me!",
    page_icon="🤖"
)

### Setting up the session state 

if 'inserted' not in st.session_state:
    ### read in txts
    with open('base.txt', 'r') as file:
        st.session_state.base_text = file.read()
    with open('knowledge.txt', 'r') as file:
        st.session_state.knowledge_text = file.read()
    with open('personalization.txt', 'r') as file:
        st.session_state.personalization_text = file.read()

    if 'k' not in st.query_params:
        st.query_params['k'] = 't'
    if 'p' not in st.query_params:
        st.query_params['p'] = 't'

    st.session_state.inserted = 0

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o-mini-2024-07-18"

if "max_messages" not in st.session_state:
    st.session_state.max_messages = 20

if 'user_info' not in st.session_state:
    st.session_state.user_info = ''

def setup_messages():
    ### k = knowledge ('f' none, otherwise climate)
    ### p = personalization ('f' none, otherwise personalization)

    if st.query_params["k"] == "f" and st.query_params["p"] == "f":
        st.session_state.system_message = st.session_state.base_text 
    elif st.query_params["k"] == "t" and st.query_params["p"] == "f":
        preamble = '''You are an expert at explaining and motivating climate action, and you advise the user on what they can do to help fight climate change. Your goal is to find a way to engage the user in climate action and educate them on what climate actions are the most effective.'''
        st.session_state.system_message = preamble + '\n\n' + st.session_state.knowledge_text + '\n\n' + st.session_state.base_text
    elif st.query_params["k"] == "f" and st.query_params["p"] == "t":
        preamble = '''You are an expert at explaining and motivating climate action, and you advise the user on what they can do to help fight climate change in their specific circumstances, which are mentioned in the user context below. Your goal is to find a way to engage the user in climate action and educate them on what climate actions are the most effective in their specific situation.'''
        st.session_state.system_message = preamble + '\n\n' + st.session_state.base_text + '\n\n' + st.session_state.personalization_text.replace('[USER_INFO]',st.session_state.user_info)
    else:
        preamble = '''You are an expert at explaining and motivating climate action, and you advise the user on what they can do to help fight climate change in their specific circumstances, which are mentioned in the user context below. Your goal is to find a way to engage the user in climate action and educate them on what climate actions are the most effective in their specific situation.'''
        st.session_state.system_message = preamble + '\n\n' + st.session_state.knowledge_text + '\n\n' + st.session_state.base_text + '\n\n' + st.session_state.personalization_text.replace('[USER_INFO]',st.session_state.user_info)

    st.session_state.messages = [{ "role": "system", "content": st.session_state.system_message}]

if 'messages' not in st.session_state:
    setup_messages()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

### App interface 

st.title("Chat with me!")
with st.expander("ℹ️ Information"):
        st.markdown(
        """- Type in the chat box to start a conversation.
- Use the *End Conversation* tab to finish and submit a conversation.
- Each conversation allows up to 10 messages, and model availability may vary during peak times."""
        )
st.write(f"You have submitted {st.session_state.inserted} conversation(s).")

if st.query_params['p'] == 't':
    st.text_area(
        "Write 3 sentences about yourself.",
        '', key='user_info',on_change=setup_messages)

# st.write(st.session_state.system_message)

for message in st.session_state.messages:
    if message['role']!='system':
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if len(st.session_state.messages) >= st.session_state.max_messages:
    st.info(
        """Notice: The maximum message limit for this demo version has been reached. Thank you for your understanding."""
    )

elif st.query_params['p'] == 't' and st.session_state.user_info == '':
    st.info('Please enter a short summary of your personal circumstances to start the conversation.')
    
st.chat_input("Ask something...",key='prompt')

if st.session_state.prompt:
    prompt = st.session_state.prompt
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

with st.expander("⏹️ End Conversation"):
    st.text_input(label="Enter your Prolific ID",key="user_id")
    st.slider('Rate the conversation from *Terrible* to *Perfect*. There are no right or wrong answers.', 0, 100, format="", key="score", value=50)
    if st.button('Submit', key=None, help=None, disabled = len(st.session_state.messages) < 2, use_container_width=True):
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
    
