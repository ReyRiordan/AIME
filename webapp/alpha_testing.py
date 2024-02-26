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

from dotenv import load_dotenv

load_dotenv()


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_URI=os.getenv("DB_URI")

client = MongoClient(DB_URI,server_api=ServerApi('1'))

try:
    client.admin.command('ping')
    print("connection successful")
except Exception as e:
    print(e)

@st.cache_data(ttl=1200)
def get_data():
    db=client["AIME"]
    items=db["Conversation"].find()
    items = list(items)
    return items

items=get_data()

collection=client["AIME"]["Conversation"]


print(len(items))
some_conversation=Interview("Rey Riordan",Patient("John Smith"))

# collection.insert_one(some_conversation.get_dict())
 

if "stage" not in st.session_state:
    st.session_state["stage"] = CHAT_SETUP

def set_stage(stage):
    st.session_state["stage"] = stage


if st.session_state["stage"] == CHAT_SETUP:
    messages = [{"role": "User", "content": "Hello, I'm Dr. Corbett. What brings you in today?"},
                {"role": "AI", "content": "Hi there, I've been having this sharp pain in my chest. It's been going on for about a day and a half now. It started off mild but it's gotten much worse today. I'm really worried because my dad died of a heart attack when he was 50."}, 
                {"role": "User", "content": "Tell me more about this sharp pain in your chest"}, 
                {"role": "AI", "content": "Well, it's right in the center of my chest. It's a stabbing kind of pain, really severe. I've never felt anything like this before. It's making me quite nervous, to be honest."}, 
                {"role": "User", "content": "Any difficulty breathing?"}, 
                {"role": "AI", "content": "Yes, sometimes it feels a bit hard to breathe, especially when I lay back. It's a bit better if I don't take deep breaths."}, 
                {"role": "User", "content": "Do you have pain anywhere else?"}, 
                {"role": "AI", "content": "Yes, I've also noticed some pain along the upper part of my back, on both shoulders."}, 
                {"role": "User", "content": "Do you have high blood pressure or high cholesterol?"}, 
                {"role": "AI", "content": "I do have high cholesterol, and I take a statin for it. But as far as I know, I don't have high blood pressure."}, 
                {"role": "User", "content": "Are there any medical issues that run in your family?"}, 
                {"role": "AI", "content": "Yes, my father died suddenly of a heart attack when he was 50 years old. And my mother was diagnosed with breast cancer two years ago."}, 
                {"role": "User", "content": "Do you drink or smoke?"}, 
                {"role": "AI", "content": "No, I've never smoked. I do enjoy a glass of wine or a cocktail during the week, but that's about it."}]

    st.session_state["interview"] = Interview("TEST", Patient("Jackie Smith"))
    for message in messages:
        if message["role"] == "User":
            st.session_state["interview"].add_message(Message("input", message["role"], message["content"]))
        elif message["role"] == "AI":
            st.session_state["interview"].add_message(Message("output", message["role"], message["content"]))
    
    set_stage(DIAGNOSIS)


if st.session_state["stage"] == DIAGNOSIS:
    st.title("Diagnosis")
    st.write("Use the interview transcription and additional patient information to provide a differential diagnosis.")
    
    for item in items:
        st.write(item['username'])

    chat_container = st.container(height=300)
    for message in st.session_state["interview"].get_messages():
        with chat_container:
            with st.chat_message(message.role):
                st.markdown(message.content)
    
    info_columns = st.columns(5)
    info_columns[1].button("View Physical", on_click=set_stage, args=[PHYSICAL_SCREEN])
    info_columns[3].button("View ECG", on_click=set_stage, args=[ECG_SCREEN])

    main_diagnosis = st.text_input(label = "Main Diagnosis:", placeholder = "Condition name")
    main_rationale = st.text_area(label = "Rationale:", placeholder = "Rationale for main diagnosis")

    input_columns = st.columns(2)
    secondary1 = input_columns[0].text_input(label = "Secondary Diagnoses:", placeholder = "Condition name")
    secondary2 = input_columns[1].text_input(label = "None", placeholder = "Condition name", label_visibility = "hidden")

    currentDateAndTime = date.datetime.now()
    date_time = currentDateAndTime.strftime("%d-%m-%y__%H-%M")
    bio = io.BytesIO()
    st.session_state["convo_file"] = create_convo_file(st.session_state["interview"])
    st.session_state["convo_file"].save(bio)
    
    button_columns = st.columns(5)
    button_columns[1].button("New Interview", on_click=set_stage, args=[SETTINGS])
    button_columns[2].download_button("Download interview", 
                    data = bio.getvalue(),
                    file_name = st.session_state["interview"].get_username() + "_"+date_time + ".docx",
                    mime = "docx")
    if button_columns[3].button("Get Feedback"):
        st.session_state["interview"].add_diagnosis(main_diagnosis, main_rationale, [secondary1, secondary2])
        set_stage(FEEDBACK_SETUP)
        st.rerun()


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
    st.session_state["interview"].add_diagnosisgrades()
    
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
    
    with diagnosis:
        diagnosis = st.session_state["interview"].get_diagnosis()
        score = st.session_state["interview"].get_diagnosisgrades().score
        maxscore = st.session_state["interview"].get_diagnosisgrades().maxscore
        st.header(f"Diagnosis: {score}/{maxscore}")
        st.divider()
        st.write("Main Diagnosis: " + diagnosis.main_diagnosis)
        st.write("Main Rationale: " + diagnosis.main_rationale)
        st.write("Secondary Diagnoses: " + ", ".join(diagnosis.secondary_diagnoses))