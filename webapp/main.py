from langchain_community.chat_models import ChatOpenAI
from langchain.chains.conversation.base import ConversationChain
from langchain.memory.buffer import ConversationBufferMemory
import time
import datetime as date
from docx import Document
import io
import os
import streamlit as st
import streamlit.components.v1 as components
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName,
    FileType, Disposition, ContentId)
from lookups import *
from website_methods import *
from website_classes import *
from audiorecorder import audiorecorder
from openai import OpenAI
import tempfile
from annotated_text import annotated_text
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


# from dotenv import load_dotenv

# load_dotenv()


# SECRETS
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LOGIN_PASS = os.getenv("LOGIN_PASS")
DB_URI=os.getenv("DB_URI")

# Establish connection to server

client = MongoClient(DB_URI,server_api=ServerApi('1'))

# Ping server on startup

try:
    client.admin.command('ping')
    print("Connection Successful")
except Exception as e:
    print(e)

# Method to get data of server

@st.cache_data(ttl=1200)
def get_data():
    db=client["AIME"]
    items=db["Conversation"].find()
    items = list(items)
    return items

# MongoDB Collection to add to

collection=client["AIME"]["Conversation"]

######### WEBSITE 

st.title("Medical Interview Simulation (BETA)")

if "stage" not in st.session_state:
    st.session_state["stage"] = LOGIN_PAGE

def set_stage(stage):
    st.session_state["stage"] = stage


if st.session_state["stage"] == LOGIN_PAGE:
    st.write("For beta testing use only.")
    
    st.session_state["username"] = st.text_input("Enter any username (does not have to be your real name):")
    password = st.text_input("Enter the password you were provided and press \"Enter\":", type = "password")
    if password:
        if not st.session_state["username"]:
            st.write("Missing username.")
        elif password == LOGIN_PASS: 
            st.write("Authentication successful!")
            time.sleep(1)
            set_stage(SETTINGS)
            st.rerun()
        else:
            st.write("Password incorrect.")


if st.session_state["stage"] == SETTINGS:
    st.session_state["interview"] = None
    st.session_state["convo_file"] = None

    chat_mode = st.selectbox("Would you like to use text or voice input for the interview?",
                             ["Text", "Voice"],
                             index = None,
                             placeholder = "Select interview mode...")
    if chat_mode == "Text": st.session_state["chat_mode"] = CHAT_INTERFACE_TEXT
    elif chat_mode == "Voice": st.session_state["chat_mode"] = CHAT_INTERFACE_VOICE
    else: st.session_state["chat_mode"] = None

    patient_name = st.selectbox("Which patient would you like to interview?", 
                                               ["John Smith", "Jackie Smith"],
                                               index = None,
                                               placeholder = "Select patient...")
    if patient_name: st.session_state["interview"] = Interview(st.session_state["username"], Patient(patient_name))

    if st.session_state["chat_mode"]: st.button("Start Interview", on_click=set_stage, args=[CHAT_SETUP])


if st.session_state["stage"] == CHAT_SETUP:
    llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model_name=CONVO_MODEL, temperature=0.0)
    st.session_state["chatbot"] = ConversationChain(llm=llm, memory=ConversationBufferMemory())
    initial_output = st.session_state["chatbot"].predict(input = st.session_state["interview"].get_patient().convo_prompt)

    st.session_state["interview"].add_message(Message("N/A", "Assistant", "You may now begin your interview with " + st.session_state["interview"].get_patient().name + ". Start by introducing yourself."))
    
    set_stage(st.session_state["chat_mode"])


if st.session_state["stage"] == CHAT_INTERFACE_TEXT:
    st.write("Click the Restart button to restart the interview. Click the End Interview button to go to the download screen.")
    # st.session_state["start_time"] = date.datetime.now()

    container = st.container(height=300)

    for message in st.session_state["interview"].get_messages():
        with container:
            with st.chat_message(message.role):
                st.markdown(message.content)

    if user_input := st.chat_input("Type here..."):
        with container:
            with st.chat_message("User"):
                st.markdown(user_input)
        st.session_state["interview"].add_message(Message("input", "User", user_input))
        output = st.session_state["chatbot"].predict(input=user_input)
        with container:
            with st.chat_message("AI"): # Needs avatar eventually
                st.markdown(output)
        st.session_state["interview"].add_message(Message("output", "AI", output))

    columns = st.columns(4)
    columns[1].button("Restart", on_click=set_stage, args=[SETTINGS])
    columns[2].button("End Interview", on_click=set_stage, args=[DIAGNOSIS])


if st.session_state["stage"] == CHAT_INTERFACE_VOICE:
    st.write("""Click the Start Recording button to start recording your voice input to the virtual patient. The button will then turn into a Stop button, which you can click when you are done talking.
             Click the Restart button to restart the interview, and the End Interview button to go to the download screen.""")

    audio = audiorecorder("Start Recording", "Stop")
    
    container = st.container(height=300)

    for message in st.session_state["interview"].get_messages():
        with container:
            with st.chat_message(message.role):
                st.markdown(message.content)

    if len(audio) > 0:
        user_input = transcribe_voice(audio, OPENAI_API_KEY)
        with container:
            with st.chat_message("User"):
                st.markdown(user_input)
        st.session_state["interview"].add_message(Message("input", "User", user_input))
        output = st.session_state["chatbot"].predict(input=user_input)
        with container:
            with st.chat_message("AI"): # Needs avatar eventually
                st.markdown(output)
        st.session_state["interview"].add_message(Message("output", "AI", output))

    columns = st.columns(4)
    columns[1].button("Restart", on_click=set_stage, args=[SETTINGS])
    columns[2].button("End Interview", on_click=set_stage, args=[DIAGNOSIS])


if st.session_state["stage"] == DIAGNOSIS:
    st.write("NO DIAGNOSIS INPUT IMPLEMENTED YET.")
    columns = st.columns(4)
    columns[1].button("View Physical", on_click=set_stage, args=[PHYSICAL_SCREEN])
    columns[2].button("View ECG", on_click=set_stage, args=[ECG_SCREEN])

    # currentDateAndTime = date.datetime.now()
    # date_time = currentDateAndTime.strftime("%d-%m-%y__%H-%M")
    bio = io.BytesIO()
    st.session_state["convo_file"] = create_convo_file(st.session_state["interview"])
    st.session_state["convo_file"].save(bio)
        
    st.download_button("Download interview", 
                    data = bio.getvalue(),
                    file_name = st.session_state["interview"].get_username() + "_" + ".docx",
                    mime = "docx")
    
    st.download_button("Download JSON",
                data=st.session_state["interview"].get_json(),
                file_name = st.session_state["interview"].get_username() + "_" + ".json",
                mime="json")
    


    st.button("Get Feedback", on_click=set_stage, args=[FEEDBACK_SETUP])
    st.button("New Interview", on_click=set_stage, args=[SETTINGS])


if st.session_state["stage"] == PHYSICAL_SCREEN:
    st.header("Physical Examination Findings")
    st.write("Here is the full physical examination for " + st.session_state["interview"].get_patient().name + ". Click the \"Back\" button to go back once you're done.")
    
    physical = st.container(border = True)
    with physical:
        physical_exam_doc = Document(st.session_state["interview"].get_patient().physical)
        for paragraph in physical_exam_doc.paragraphs:
            st.write(paragraph.text)
    
    st.button("Back", on_click=set_stage, args=[DIAGNOSIS])
    

if st.session_state["stage"] == ECG_SCREEN:
    st.header("ECG Chart")
    st.write("Here is the ECG for " + st.session_state["interview"].get_patient().name + ". Click the \"Back\" button to go back once you're done.")
    
    st.image(st.session_state["interview"].get_patient().ECG)

    st.button("Back", on_click=set_stage, args=[DIAGNOSIS])


if st.session_state["stage"] == FEEDBACK_SETUP:
    annotate(st.session_state["interview"], OPENAI_API_KEY)
    st.session_state["interview"].add_datagrades()
    
    set_stage(FEEDBACK_SCREEN)


if st.session_state["stage"] == FEEDBACK_SCREEN:
    # tabs for feedback types
    data, diagnosis, empathy = st.tabs(["Data Acquisition", "Diagnosis", "Empathy"])
    
    with data:
        chat_container = st.container(height=300)
        for message in st.session_state["interview"].get_messages():
                with chat_container:
                    with st.chat_message(message.role):
                        if message.annotation is None:
                            st.markdown(message.content)
                        else:
                            annotated_text((message.content, message.annotation, message.highlight))

        for category in st.session_state["interview"].get_categories():
            if category.tab == "data":
                display_datagrades(st.session_state["interview"].get_datagrades(), category)

    st.button("Go to End Screen", on_click=set_stage, args=[FINAL_SCREEN])


if st.session_state["stage"] == FINAL_SCREEN: 
    st.write("Click the download button to download your most recent interview as a word file. Click the New Interview button to go back to the chat interface and keep testing.")
    currentDateAndTime = date.datetime.now()
    date_time = currentDateAndTime.strftime("%d-%m-%y__%H-%M")
    bio = io.BytesIO()
    st.session_state["convo_file"] = create_convo_file(st.session_state["interview"])
    st.session_state["convo_file"].save(bio)
        
    st.download_button("Download interview", 
                    data = bio.getvalue(),
                    file_name = st.session_state["interview"].get_username() + "_"+date_time + ".docx",
                    mime = "docx")
    
    
    collection.update_one(st.session_state["interview"].get_dict(),upsert=True)

    send_email(bio, EMAIL_TO_SEND, st.session_state["interview"].get_username(), date_time, None)
        

    st.download_button("Download JSON",
                data=st.session_state["interview"].get_json(),
                file_name = st.session_state["interview"].get_username() + "_"+date_time + ".json",
                mime="json")

    st.button("New Interview", on_click=set_stage, args=[SETTINGS])