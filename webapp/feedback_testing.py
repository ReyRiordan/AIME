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

# from dotenv import load_dotenv

# load_dotenv()


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
                {"role": "AI", "content": "I came to the hospital because I'm experiencing a heaviness in my chest. It came on gradually while I was sitting at my desk at home about 2 hours ago. I'm really worried because my father died suddenly of a heart attack when he was 50."}, 
                {"role": "User", "content": "Sorry, so sorry to hear about your father. Can you tell me more about this heaviness?"}, 
                {"role": "AI", "content": "It started as a pretty severe heaviness or pressure in the center of my chest. It's gotten a bit better since it first started, but there's still some heaviness there. I was also feeling a little nauseated and sweaty before coming in, but I feel a bit better now."}, 
                {"role": "User", "content": "I see. Have you ever had anything like this happen to you before?"}, 
                {"role": "AI", "content": "No, I've never had chest pain or pressure like this before. Sometimes I get a milder discomfort in my chest when walking up hills, which I thought was just heartburn or a stomach issue. But nothing as severe as this heaviness I'm feeling now."}, 
                {"role": "User", "content": "Okay, and does it seem to come and go or is it constant?"}, 
                {"role": "AI", "content": "It's been pretty constant since it started, not really coming and going."}, 
                {"role": "User", "content": "have you ever smoked?"}, 
                {"role": "AI", "content": "Yes, I used to smoke. I started when I was 19 in college and smoked about a pack a day until I quit 5 years ago."}, 
                {"role": "User", "content": "Okay, and any alcohol or drug use?"}, 
                {"role": "AI", "content": "I don't use any drugs, but I do drink socially - maybe 2 glasses of wine or a cocktail during the week and a bit more on weekends."}, 
                {"role": "User", "content": "Alright, just last thing, are there any other symptoms that you think I might need to know about? Any other medical issues that you'd like to make me aware of?"}, 
                {"role": "AI", "content": "Well, I've had some difficulty maintaining an erection for the past 2 years that I've been meaning to talk to my doctor about. And I do get pain and cramping in my left calf when I walk for a while, but it goes away when I stop walking."}]
    
    st.session_state["interview"] = Interview.build(username="TEST", patient=Patient.build(name="John Smith"))
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
    summary = layout1[0].text_area(label = "Interpretive Summary:", placeholder = "Interpretive summary for patient", height = 200)
    layout11 = layout1[0].columns([1, 1, 1])
    potential1 = layout11[0].text_input(label = "Potential Diagnoses:", placeholder = "First condition name")
    potential2 = layout11[1].text_input(label = "None", placeholder = "Second condition name", label_visibility = "hidden")
    potential3 = layout11[2].text_input(label = "None", placeholder = "Third condition name", label_visibility = "hidden")
    rationale = layout1[0].text_area(label = "Rationale:", placeholder = "Rationale for diagnosis")
    final = layout1[0].text_input(label = "Final Diagnosis:", placeholder = "Condition name")

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
        st.session_state["interview"].add_diagnosis_inputs(summary, [potential1, potential2, potential3], rationale, final)
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
    layout1 = st.columns([7, 1])
    layout1[0].write("blah blah blah")
    layout1[1].button("Go to End Screen", on_click=set_stage, args=[FINAL_SCREEN])
    
    # Let the display methods cook
    display_Interview(st.session_state["interview_dict"])


# if st.session_state["stage"]==VIEW_INTERVIEWS:
#     display_interview(dict_to_interview(all_interviews[st.session_state["interview_display_index"]]))

#     button_columns=st.columns(5) 

#     if button_columns[0].button("Previous Interview") and st.session_state["interview_display_index"]>0:
#         st.session_state["interview_display_index"]-=1
#     if button_columns[4].button("Next Interview") and st.session_state["interview_display_index"]<len(all_interviews)-1:
#         st.session_state["interview_display_index"]+=1
#         print(st.session_state["interview_display_index"])

#     button_columns[2].button("Back to previous page", on_click=set_stage, args=[DIAGNOSIS])