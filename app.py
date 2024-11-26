import streamlit as st
from openai import OpenAI
from datetime import datetime
import time
import numpy as np

st.set_page_config(
    page_title="Chat with me!",
    page_icon="🤖"
)
st.markdown(
    """ <style>
            div[role="radiogroup"] >  :first-child{
                display: none !important;
            }
        </style>
        """,
    unsafe_allow_html=True
)

### Setting up the session state 

if 'inserted' not in st.session_state:
    ### read in txts
    with open('base.txt', 'r') as file:
        st.session_state.base_text = file.read()
    with open('knowledge.txt', 'r') as file:
        st.session_state.knowledge_text = "" # file.read()
    with open('personalization.txt', 'r') as file:
        st.session_state.personalization_text = file.read()

    st.session_state.actions_list = ['None'] + np.random.permutation(
        ["Living car-free", "Owning or leasing an electric car", "Avoiding one long-haul flight", "Purchasing renewable electricity", "Eating a vegan diet", "Installing heat pumps", "Eating a vegetarian diet", "Car-pooling", "Reducing food waste", "Eating seasonally", "Turning down the heating", "Buying fewer things", "Using energy-efficient appliances", "Recycling"]
    )
    st.session_state.inserted = 0
    st.session_state["openai_model"] = "gpt-4o-mini-2024-07-18"
    st.session_state.max_messages = 20
    st.session_state.user_id = ''
    st.session_state.climate_actions = []
    st.session_state.age = 0
    st.session_state.gender = ''
    st.session_state.education = ''

    st.session_state.submitted = False

if 'k' not in st.query_params:
    st.query_params['k'] = 't'
if 'p' not in st.query_params:
    st.query_params['p'] = 't'

if 'user_info' not in st.session_state:
    st.session_state.user_info = ''

def setup_messages():
    ### k = knowledge ('f' none, otherwise climate)
    ### p = personalization ('f' none, otherwise personalization)

    if st.query_params["k"] == "f" and st.query_params["p"] == "f":
        st.session_state.system_message = st.session_state.base_text 
    elif st.query_params["k"] == "t" and st.query_params["p"] == "f":
        st.session_state.system_message = st.session_state.knowledge_text + '\n\n' + st.session_state.base_text
    elif st.query_params["k"] == "f" and st.query_params["p"] == "t":
        st.session_state.system_message = st.session_state.personalization_text.replace('[USER_INFO]',st.session_state.user_info) + '\n\n' + st.session_state.base_text
    else:
        climate_actions = ", ".join(st.session_state.climate_actions)
        personalization_text = st.session_state.personalization_text.replace('[AGE]',str(st.session_state.age)).replace('[GENDER]',st.session_state.gender).replace('[EDUCATION]',st.session_state.education).replace('[CLIMATE_ACTIONS]',climate_actions).replace('[LOCALITY]',st.session_state.locality).replace('[PROPERTY]',st.session_state.property).replace('[INCOME]',st.session_state.income)
        st.session_state.system_message = st.session_state.knowledge_text + '\n\n' + personalization_text.replace('[USER_INFO]',st.session_state.user_info)  + '\n\n' + st.session_state.base_text

    st.session_state.messages = [{ "role": "system", "content": st.session_state.system_message}]

if 'messages' not in st.session_state:
    setup_messages()

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

### App interface 

st.title("Chat with me!")
with st.expander("Information"):
        st.markdown(
        f"""- Type in the chat box to start a conversation.
- Use the *End Conversation* button to finish and submit.
- Each conversation allows up to 10 messages.
- You have submitted {st.session_state.inserted} conversation(s).
- The website may be unavailable if too many people use it simultaneously."""
)

with st.expander("Form",expanded=not st.session_state.submitted):
    with st.form("Form",border=False):
        st.text("How old are you?",key="age")
        st.radio("Do you describe yourself as a man, a woman, or in some other way?", 
                 ['','Man', 'Woman', 'Other'], key="gender")
        st.radio("What is the highest level of education you completed?", 
                 ['', 
                  'Did not graduate high school', 
                  'High school graduate, GED, or alternative', 
                  'Some college, or associates degree',
                  "Bachelor's (college) degree or equivalent",
                  'Graduate degree (e.g., Master’s degree, MBA)',
                  'Doctorate degree (e.g., PhD, MD)'], key="education")
        st.radio("What type of a community do you live in?", 
                 ['', 'Urban','Suburban','Rural','Other'], key="locality")
        st.radio("Do you own or rent the home in which you live?", 
                 ['', 'Own','Rent','Neither (I live rent-free)',
                  'Other' ], key="property")
        st.radio("What was your total household income before taxes during the past 12 months?",
                    ['','Less than $25,000','$25,000 to $49,999','$50,000 to $74,999','$75,000 to $99,999','$100,000 to $149,999','$150,000 or more'], key="income")
        st.multiselect('What climate actions are you currently taking?',
                       st.session_state.actions_list,
                       key="climate_actions"
        )
        st.text_area(
        "Write at least three sentences about yourself.",
        '', key='user_info')

        columns_form = st.columns((1,1,1))
        with columns_form[2]:
            submitted = st.form_submit_button("Submit",use_container_width=True)

        if submitted:
            st.session_state.submitted = True
            setup_messages()

st.write(st.session_state.system_message)

for message in st.session_state.messages:
    if message['role']!='system':
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if len(st.session_state.messages) >= st.session_state.max_messages:
    st.info(
        "You have reached the limit of messages for this conversation. Please submit the conversation to start a new one."
    )

elif st.session_state.user_info == '':
   st.info('Please complete the form above to start a conversation.')

elif prompt := st.chat_input("Ask something..."):   

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

@st.dialog('Submit conversation')
def submit():
    st.session_state.user_id = st.text_input(label="Enter your Prolific ID", value=st.session_state.user_id)
    st.slider('You must rate the conversation from *Terrible* to *Perfect* to submit.', 0, 100, format="", key="score", value=50)
    st.text_area('Any feedback?',key="feedback")
    if st.button('Submit', key=None, help=None, use_container_width=True, disabled=st.session_state.user_id=="" or st.session_state.score==50):
        submission_time = datetime.now().strftime('%Y%m-%d%H-%M%S')

        user_data={"user_id":st.session_state.user_id,
                    "conversation":st.session_state.messages,
                    "score":st.session_state.score,
                    "time":submission_time,
                    "user_info":st.session_state.user_info,
                    "feedback":st.session_state.feedback,
                    "condition":f"k{st.query_params['k']}p{st.query_params['p']}",
                    "age":st.session_state.age,
                    "gender":st.session_state.gender,
                    "education":st.session_state.education,
                    "climate_actions":st.session_state.climate_actions,
                    "inserted":st.session_state.inserted}
        
        from pymongo.mongo_client import MongoClient
        from pymongo.server_api import ServerApi
        with MongoClient(st.secrets["mongo"],server_api=ServerApi('1')) as client:
                db = client.chat
                collection = db.app
                collection.insert_one(user_data)  
                st.session_state.inserted += 1
                
                st.success('Your conversation has been submitted.', icon="✅")

                time.sleep(1)
                setup_messages()
                st.rerun()

if len(st.session_state.messages) > 2:
    columns = st.columns((1,1,1))
    with columns[2]:
        if st.button("End Conversation",use_container_width=True):
            submit()
    
