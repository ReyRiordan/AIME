from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
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


# SECRETS
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LOGIN_PASS = "corbetsi"

BETA_PATIENT = "John Smith"
BASE = "./Prompts/Base_1-15.txt"
CONTEXT = "./Prompts/JohnSmith_sectioned.txt"

st.title("Medical Interview Simulation (BETA)")

if "stage" not in st.session_state:
    st.session_state["stage"] = LOGIN_PAGE

def set_stage(stage):
    st.session_state["stage"] = stage


if st.session_state["stage"] == LOGIN_PAGE:
    st.write("For beta testing use only.")
    
    st.session_state["username"] = st.text_input("Enter any username (does not have to be your real name) and press \"Enter\":")
    if st.session_state["username"]:
        password = st.text_input("Enter the password you were provided and press \"Enter\":")
        if password == LOGIN_PASS: 
            st.write("Authentication successful!")
            time.sleep(2)
            set_stage(CHAT_SETUP)
            st.rerun()

if st.session_state["stage"] == CHAT_SETUP:
    llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model_name=MODEL, temperature=0.0)
    st.session_state["conversation"] = ConversationChain(llm=llm, memory=ConversationBufferMemory())
    with open(BASE, "r", encoding="utf8") as base_file:
        base = base_file.read()
    base = base.replace("{patient}", BETA_PATIENT)
    with open(CONTEXT, "r", encoding="utf8") as context_file:
        context = context_file.read()
    prompt_input = str(base + context)
    initial_output = st.session_state["conversation"].predict(input = prompt_input)

    st.session_state["messages"] = []
    st.session_state["messages"].append({"role": "Assistant", "content": "You may now begin your interview with " + BETA_PATIENT + "."})
    
    set_stage(CHAT_INTERFACE)

if st.session_state["stage"] == CHAT_INTERFACE:
    st.write("Click the Restart button to restart the interview. Click the End Interview button to go to the download screen.")
    
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input := st.chat_input("Type here..."):
        with st.chat_message(st.session_state["username"]):
            st.markdown(user_input)
        st.session_state["messages"].append({"role": st.session_state["username"], "content": user_input})
        output = st.session_state["conversation"].predict(input=user_input)
        with st.chat_message(BETA_PATIENT):
            st.markdown(output)
            st.session_state["messages"].append({"role": BETA_PATIENT, "content": output})

    st.button("Restart", on_click=set_stage, args=[CHAT_SETUP])
    st.button("End Interview", on_click=set_stage, args=[FINAL_SCREEN])

if st.session_state["stage"] == FINAL_SCREEN: 
    st.write("Click the download button to download your most recent interview as a word file. Click the New Interview button to go back to the chat interface and keep testing.")

    currentDateAndTime = date.datetime.now()
    date_time = currentDateAndTime.strftime("%d-%m-%y__%H-%M")

    bio = io.BytesIO()
    st.session_state["interview"] = methods.create_interview_file(st.session_state["username"], 
                                                                  BETA_PATIENT, 
                                                                  st.session_state["messages"])
    st.session_state["interview"].save(bio)

    st.download_button("Download interview", 
                        data=bio.getvalue(),
                        file_name=st.session_state["username"]+"_"+date_time+".docx",
                        mime="docx")

    st.button("New Interview", on_click=set_stage, args=[CHAT_SETUP])