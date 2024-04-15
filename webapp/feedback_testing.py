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
from audiorecorder import audiorecorder
from openai import OpenAI
import tempfile
from annotated_text import annotated_text
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from lookups import *
from web_classes import *
from web_methods import *

from dotenv import load_dotenv

load_dotenv()


# client = MongoClient(DB_URI,server_api=ServerApi('1'))

# try:
#     client.admin.command('ping')
#     print("connection successful")
# except Exception as e:
#     print(e)

# @st.cache_data(ttl=1200)
# def get_data():
#     db=client["AIME"]
#     items=db["Conversation"].find()
#     items = list(items)
#     return items


# collection=client["AIME"]["Conversation"]
# all_interviews=get_data()
# if "interview_display_index" not in st.session_state:
#     st.session_state["interview_display_index"]=0

# some_conversation=Interview("Rey Riordan",Patient("John Smith"))

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
    st.session_state["random_patient"]=Patient.build(name="Jackie Smith")
    st.session_state["interview"] = Interview.build(username="TEST", patient=Patient.build(name="Jackie Smith"))
    for message in messages:
        if message["role"] == "User":
            st.session_state["interview"].add_message(Message(type="input", role=message["role"], content=message["content"]))
            
        elif message["role"] == "AI":
            st.session_state["interview"].add_message(Message(type="output", role=message["role"], content=message["content"]))
    
    set_stage(DIAGNOSIS)


if st.session_state["stage"] == DIAGNOSIS:
    st.title("Diagnosis")
    st.write("Use the interview transcription and additional patient information to provide an interpretative summary and differential diagnosis.")

    # 2 column full width layout
    layout1 = st.columns([1, 1])

    # User inputs
    interpretative_summary = layout1[0].text_area(label = "Interpretive Summary:", placeholder = "Interpretive summary for patient", height = 200)
    main_diagnosis = layout1[0].text_input(label = "Main Diagnosis:", placeholder = "Condition name")
    main_rationale = layout1[0].text_area(label = "Rationale:", placeholder = "Rationale for main diagnosis")
    layout11 = layout1[0].columns([1, 1])
    secondary1 = layout11[0].text_input(label = "Secondary Diagnoses:", placeholder = "Condition name")
    secondary2 = layout11[1].text_input(label = "None", placeholder = "Condition name", label_visibility = "hidden")

    # 3 buttons at bottom
    layout12 = layout1[0].columns([1, 1, 1])
    # New Interview
    layout12[0].button("New Interview", on_click=set_stage, args=[SETTINGS])
    # Download Interview
    currentDateAndTime = date.datetime.now()
    date_time = currentDateAndTime.strftime("%d-%m-%y__%H-%M")
    bio = io.BytesIO()
    st.session_state["convo_file"] = create_convo_file(st.session_state["interview"].get_username(), 
                                                       st.session_state["interview"].get_patient().name, 
                                                       [message.get_dict() for message in st.session_state["interview"].get_messages()])
    st.session_state["convo_file"].save(bio)
    layout12[1].download_button("Download interview", 
                                data = bio.getvalue(), 
                                file_name = st.session_state["interview"].get_username() + "_"+date_time + ".docx", 
                                mime = "docx")
    # Get Feedback
    if layout12[2].button("Get Feedback"): 
        st.session_state["interview"].add_user_diagnosis(interpretative_summary, main_diagnosis, main_rationale, [secondary1, secondary2])
        set_stage(FEEDBACK_SETUP)
        st.rerun()
    
    # Interview transcription
    chat_container = layout1[1].container(height=400)
    for message in st.session_state["interview"].get_messages():
        with chat_container:
            with st.chat_message(message.role):
                st.markdown(message.content)
    # Physical Examination
    with layout1[1].expander("Physical Examination"):
        physical_exam_doc = Document(st.session_state["interview"].get_patient().physical)
        for paragraph in physical_exam_doc.paragraphs:
            st.write(paragraph.text)
    # ECG
    with layout1[1].expander("ECG"):
        st.image(st.session_state["interview"].get_patient().ECG)


if st.session_state["stage"] == FEEDBACK_SETUP:
    st.title("Processing feedback...")
    st.write("This might take a few minutes.")
    st.session_state["interview"].add_feedback()
    st.json(st.session_state["interview"].model_dump_json())
    st.session_state["interview_dict"] = st.session_state["interview"].get_dict()
    
    set_stage(FEEDBACK_SCREEN)
    st.rerun()


if st.session_state["stage"] == FEEDBACK_SCREEN:
    st.title("Feedback")
    # Let the display methods cook
    display_Interview(st.session_state["interview_dict"])

    st.button("Go to End Screen", on_click=set_stage, args=[FINAL_SCREEN])


# if st.session_state["stage"]==VIEW_INTERVIEWS:
#     display_interview(dict_to_interview(all_interviews[st.session_state["interview_display_index"]]))

#     button_columns=st.columns(5) 

#     if button_columns[0].button("Previous Interview") and st.session_state["interview_display_index"]>0:
#         st.session_state["interview_display_index"]-=1
#     if button_columns[4].button("Next Interview") and st.session_state["interview_display_index"]<len(all_interviews)-1:
#         st.session_state["interview_display_index"]+=1
#         print(st.session_state["interview_display_index"])

#     button_columns[2].button("Back to previous page", on_click=set_stage, args=[DIAGNOSIS])