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
from constants import *
import website_methods as methods
import descriptions
from audiorecorder import audiorecorder
import openai
import tempfile
from virtual_patient.patients import GPT_Patient
from annotated_text import annotated_text
from website_classes import Message



# SECRETS
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LOGIN_PASS = "corbetsi"

st.title("Medical Interview Simulation (BETA)")

if "stage" not in st.session_state:
    st.session_state["stage"] = LOGIN_PAGE

def set_stage(stage):
    st.session_state["stage"] = stage


if st.session_state["stage"] == LOGIN_PAGE:
    st.write("For beta testing use only.")
    
    st.session_state["username"] = st.text_input("Enter any username (does not have to be your real name) and press \"Enter\":")
    if st.session_state["username"]:
        password = st.text_input("Enter the password you were provided and press \"Enter\":", type = "password")
        if password == LOGIN_PASS: 
            st.write("Authentication successful!")
            time.sleep(2)
            set_stage(SETTINGS)
            st.rerun()


if st.session_state["stage"] == SETTINGS:
    st.session_state["messages"] = []
    st.session_state["interview"] = None

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
    if patient_name: st.session_state["patient"] = GPT_Patient(patient_name)

    if st.session_state["chat_mode"]: st.button("Start Interview", on_click=set_stage, args=[CHAT_SETUP])


if st.session_state["stage"] == CHAT_SETUP:
    llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model_name=MODEL, temperature=0.0)
    st.session_state["conversation"] = ConversationChain(llm=llm, memory=ConversationBufferMemory())
    initial_output = st.session_state["conversation"].predict(input = st.session_state["patient"].initial_input)

    st.session_state["messages"].append(Message("N/A", "Assistant", "You may now begin your interview with " + st.session_state["patient"].name + ". Start by introducing yourself."))
    
    set_stage(st.session_state["chat_mode"])


if st.session_state["stage"] == CHAT_INTERFACE_TEXT:
    st.write("Click the Restart button to restart the interview. Click the End Interview button to go to the download screen.")
    
    container = st.container(height=300)

    for message in st.session_state["messages"]:
        with container:
            with st.chat_message(message.role):
                st.markdown(message.content)

    if user_input := st.chat_input("Type here..."):
        with container:
            with st.chat_message("User"):
                st.markdown(user_input)
        st.session_state["messages"].append(Message("input", "User", user_input))
        output = st.session_state["conversation"].predict(input=user_input)
        with container:
            with st.chat_message("AI"): # Needs avatar eventually
                st.markdown(output)
        st.session_state["messages"].append(Message("output", "AI", output))

    columns = st.columns(4)
    columns[1].button("Restart", on_click=set_stage, args=[SETTINGS])
    columns[2].button("End Interview", on_click=set_stage, args=[FINAL_SCREEN])


if st.session_state["stage"] == CHAT_INTERFACE_VOICE:
    st.write("""Click the Start Recording button to start recording your voice input to the virtual patient. The button will then turn into a Stop button, which you can click when you are done talking.
             Click the Restart button to restart the interview, and the End Interview button to go to the download screen.""")

    audio = audiorecorder("Start Recording", "Stop")
    
    container = st.container(height=300)

    for message in st.session_state["messages"]:
        with container:
            with st.chat_message(message.role):
                st.markdown(message.content)

    if len(audio) > 0:
        user_input = methods.transcribe_voice(audio, OPENAI_API_KEY)
        with container:
            with st.chat_message("User"):
                st.markdown(user_input)
        st.session_state["messages"].append(Message("input", "User", user_input))
        output = st.session_state["conversation"].predict(input=user_input)
        with container:
            with st.chat_message("AI"): # Needs avatar eventually
                st.markdown(output)
        st.session_state["messages"].append(Message("output", "AI", output))

    columns = st.columns(4)
    columns[1].button("Restart", on_click=set_stage, args=[SETTINGS])
    columns[2].button("End Interview", on_click=set_stage, args=[FINAL_SCREEN])


if st.session_state["stage"] == FEEDBACK_SETUP:
    methods.annotate(st.session_state["patient"], st.session_state["messages"], OPENAI_API_KEY)
    st.set_stage(FEEDBACK_SCREEN)


if st.session_state["stage"] == FEEDBACK_SCREEN:
    data_acquisition, diagnosis, empathy = st.tabs(["Data Acquisition", "Diagnosis", "Empathy"])
    
    with data_acquisition:
        chat_container = st.container(height=300)
        for message in st.session_state["messages"]:
                with chat_container:
                    with st.chat_message(message.role):
                        if message.annotation is None:
                            st.markdown(message.content)
                        else:
                            annotated_text((message.content, message.annotation, message.color))
    
    st.button("Go to End Screen", on_click=set_stage, args=[FINAL_SCREEN])


if st.session_state["stage"] == FINAL_SCREEN: 
    st.write("Click the download button to download your most recent interview as a word file. Click the New Interview button to go back to the chat interface and keep testing.")
    currentDateAndTime = date.datetime.now()
    date_time = currentDateAndTime.strftime("%d-%m-%y__%H-%M")

    bio = io.BytesIO()
    st.session_state["grading_results"]=""
    st.session_state["interview"] = methods.create_interview_file(st.session_state["username"], 
                                                                  st.session_state["patient"].name, 
                                                                  st.session_state["messages"], 
                                                                  st.session_state["grading_results"])
    st.session_state["interview"].save(bio)

    st.download_button("Download interview", 
                        data=bio.getvalue(),
                        file_name=st.session_state["username"]+"_"+date_time+".docx",
                        mime="docx")

    st.button("New Interview", on_click=set_stage, args=[SETTINGS])