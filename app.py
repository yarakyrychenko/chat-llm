import streamlit as st
from openai import OpenAI
from datetime import datetime
import time

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
    with open('personalization.txt', 'r') as file:
        st.session_state.personalization_text = file.read()

    # web app state
    st.session_state.inserted = 0
    st.session_state.submitted = False
    st.session_state["openai_model"] = "gpt-4o-mini-2024-07-18"
    st.session_state.max_messages = 40
    st.session_state.messages = []
    st.session_state.OpenAIclient = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    # user info state
    st.session_state.user_id = ''
    st.session_state.climate_actions = ''
    st.session_state.age = ''
    st.session_state.gender = ''
    st.session_state.education = ''
    st.session_state.locality = ''
    st.session_state.zipcode = ''
    st.session_state.property = ''
    st.session_state.income = ''
    st.session_state.user_info = ''

    # timers
    st.session_state.start_time = datetime.now()
    st.session_state.convo_start_time = ''

if 'p' not in st.query_params:
    st.query_params['p'] = 't'

def setup_messages():
    ### p = personalization ('f' none, otherwise personalization)

    if st.query_params["p"] == "f":
        st.session_state.system_message = st.session_state.base_text 
    else:
        personalization_text = st.session_state.personalization_text.replace('[AGE]',str(st.session_state.age)).replace('[GENDER]',st.session_state.gender).replace('[EDUCATION]',st.session_state.education).replace('[CLIMATE_ACTIONS]',st.session_state.climate_actions).replace('[LOCALITY]',st.session_state.locality).replace('[PROPERTY]',st.session_state.property).replace('[INCOME]',st.session_state.income).replace('[ZIPCODE]',st.session_state.zipcode)

        st.session_state.system_message = personalization_text.replace('[USER_INFO]',st.session_state.user_info)  + '\n\n' + st.session_state.base_text

    st.session_state.messages = [{ "role": "system", "content": st.session_state.system_message}]
    st.session_state.convo_start_time = datetime.now()

### App interface 

st.title("Chat with me!")
with st.expander("Information"):
        st.markdown(
        f""" - Complete and submit the from. 
- Type in the chat box to start a conversation.
- Use the *End Conversation* button to finish and submit.
- Each conversation allows up to 20 messages.
- You have submitted {st.session_state.inserted} conversation(s).
- The website may be unavailable if too many people use it simultaneously."""
)

with st.expander("Form",expanded=not st.session_state.submitted):
    with st.form("Form",border=False):
        st.text_input("How old are you?",key="age")
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
        st.text_input("What is your US Zip Code?", key="zipcode")
        st.radio("Do you own or rent the home in which you live?", 
                 ['', 'Own','Rent','Neither (I live rent-free)',
                  'Other' ], key="property")
        st.radio("What was your total household income before taxes during the past 12 months?",
                    ['','Less than \$25,000','\$25,000 to \$49,999','\$50,000 to \$74,999','\$75,000 to \$99,999','\$100,000 to \$149,999','\$150,000 or more'], key="income")
        st.text_area('Please describe any actions you are taking to address climate change? Write "None" if you are not taking any.',
                       key="climate_actions"
        )
        st.text_area(
        "Write at least two sentences about yourself. You can write about your job, hobbies, living arrangements or any other information you think might be relevant. *Do not write anything that could identify you, such as your name or address.*",
        '', key='user_info')

        columns_form = st.columns((1,1,1))
        with columns_form[2]:
            submitted = st.form_submit_button("Submit",use_container_width=True,
                                              enter_to_submit=False)

        all_form_completed = st.session_state.age != '' and st.session_state.gender != '' and st.session_state.education != '' and st.session_state.locality != '' and st.session_state.zipcode != '' and st.session_state.property != '' and st.session_state.income != '' and st.session_state.climate_actions != '' and st.session_state.user_info != ''

        if submitted and all_form_completed:
            st.session_state.submitted = True
            setup_messages()
        elif submitted and not all_form_completed:
            st.warning('Please complete every entry of the form and submit again to start a conversation.')

#st.write(st.session_state.system_message)

for message in st.session_state.messages:
    if message['role']!='system':
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if len(st.session_state.messages) >= st.session_state.max_messages:
    st.info(
        "You have reached the limit of messages for this conversation. Please submit the conversation to start a new one."
    )

elif prompt := st.chat_input("Ask something..."):   

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            stream = st.session_state.OpenAIclient.chat.completions.create(
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
        submission_date = datetime.now() #.strftime("%Y-%m-%d %H:%M:%S")

        user_data={"user_id":st.session_state.user_id,
                    "conversation":st.session_state.messages,
                    "score":st.session_state.score,
                    "user_info":st.session_state.user_info,
                    "feedback":st.session_state.feedback,
                    "condition":f"p{st.query_params['p']}",
                    "age":st.session_state.age,
                    "gender":st.session_state.gender,
                    "education":st.session_state.education,
                    "locality":st.session_state.locality,
                    "zipcode":st.session_state.zipcode,
                    "property":st.session_state.property,
                    "income":st.session_state.income,
                    "climate_actions":st.session_state.climate_actions,
                    "inserted":st.session_state.inserted,
                    "start_time":st.session_state.start_time,
                    "convo_start_time":st.session_state.convo_start_time,
                    "submission_time":submission_date,}
        
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
    
