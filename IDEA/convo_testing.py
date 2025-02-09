import time
import datetime as date
from docx import Document
import io
import os
import streamlit as st
import streamlit.components.v1 as components
# import streamlit_authenticator as auth
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

st.set_page_config(page_title = "AIME",
                   page_icon = "🧑‍⚕️",
                   layout = "wide",
                   initial_sidebar_state="collapsed")

if "stage" not in st.session_state:
    st.session_state["stage"] = LOGIN_PAGE

def set_stage(stage):
    st.session_state["stage"] = stage

if st.session_state["stage"] == LOGIN_PAGE:
    st.write("Welcome, and thank you for volunteering to participate in this beta test! This is an application where you will virtually simulate an interview with a patient, provide a differential diagnosis for them, and then automatically receive grading and feedback based on your performance.")
    st.write("Please follow the directions on each page to work through the whole application, and take notes on where there is potential room for improvement.")
    st.write("Begin by logging in!")
    
    layout1 = st.columns([2, 3, 2])
    with layout1[1]:
        st.title("Virtual Patient (BETA)")
        st.write("For beta testing use only.")

        username = st.text_input("Username:")
        password = st.text_input("Password:", type = "password")

        layout12b = layout1[1].columns(5)
        if layout12b[2].button("Log in"):
            if username and password == LOGIN_PASS:
                st.session_state["username"] = username
                st.write("Authentication successful!")
                time.sleep(1)
                set_stage(CHAT_SETUP)
                st.rerun()
            else:
                st.write("Password incorect.")


if st.session_state["stage"] == CHAT_SETUP:
    st.session_state["interview"] = None
    st.session_state["messages"] = []
    st.session_state["convo_memory"] = []
    st.session_state["convo_summary"]=""
    st.session_state["convo_file"] = None
    st.session_state["convo_prompt"] = ""
    st.session_state["sent"] = False
    st.session_state["start_time"] = date.datetime.now()
    st.session_state["tokens"] = {"convo": {"input": 0, "output": 0},
                                  "class": {"input": 0, "output": 0},
                                  "diag": {"input": 0, "output": 0}}

    patient_name = "Jeffrey Smith"

    st.session_state["interview"] = Interview.build(username = st.session_state["username"], 
                                                    patient = Patient.build(patient_name))

    st.session_state["sent"]==False

    st.session_state["convo_prompt"] = st.session_state["interview"].patient.convo_prompt
    if(st.session_state["sent"]==False):
        st.session_state["interview"].start_time = str(st.session_state["start_time"])
        # collection.insert_one(st.session_state["interview"].model_dump())
        st.session_state["sent"]==True

    set_stage(CHAT_INTERFACE_VOICE)


if st.session_state["stage"] == CHAT_INTERFACE_VOICE:
    layout1 = st.columns([1, 3, 1])
    with layout1[1]:
        st.title("Interview")
        st.write("You may now begin your interview with " + st.session_state["interview"].patient.id + ". Start by introducing yourself.")
        st.write("""Click the Start Recording button to start recording your voice input to the virtual patient.
                The button will then turn into a Stop button, which you can click when you are done talking.
                Click the Restart button to restart the interview, and the End Interview button to go to the download screen.""")

        audio = audiorecorder("Start Recording", "Stop")
        
        container = st.container(height=300)

        for message in st.session_state["interview"].messages:
            with container:
                with st.chat_message(message.role):
                    st.markdown(message.content)

        if len(audio) > 0:
            user_input = transcribe_voice(audio)
            with container:
                with st.chat_message("User"):
                    st.markdown(user_input)
            
            response, speech = get_chat_output(user_input)

            with container:
                with st.chat_message("AI"): # Needs avatar eventually
                    st.markdown(response)
                    play_voice(speech)

        columns = st.columns(4)
        columns[1].button("Restart", on_click=set_stage, args=[SETTINGS])
        columns[2].button("End Interview", on_click=set_stage, args=[KEY_PHYSICALS])