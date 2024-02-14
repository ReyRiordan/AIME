from langchain_community.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
import openai
from audiorecorder import audiorecorder
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
from webapp.lookups import *
import website_methods as methods
import unused.descriptions as descriptions
import sys
sys.path.append("/mount/src/aime")
from virtual_patient.patients import GPT_Patient


# SECRETS
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
os.environ["SENDGRID_API_KEY"] = st.secrets["SENDGRID_API_KEY"]
os.environ["LOGIN_PASS"] = st.secrets["LOGIN_PASS"]
LOGIN_PASS = os.getenv("LOGIN_PASS")


st.title("Medical Interview Simulation")

if "stage" not in st.session_state:
    st.session_state["stage"] = LOGIN_PAGE

def set_stage(stage):
    st.session_state["stage"] = stage


if st.session_state["stage"] == LOGIN_PAGE:
    st.write(descriptions.get("intro"))
    
    st.session_state["username"] = st.text_input("Enter any username (does not have to be your real name) and press \"Enter\":")
    if st.session_state["username"]:
        password = st.text_input("Enter the password you were provided and press \"Enter\":")
        if password == LOGIN_PASS: 
            st.write("Authentication successful!")
            time.sleep(2)
            set_stage(SETTINGS)
            st.rerun()


if st.session_state["stage"] == SETTINGS:
    st.write(descriptions.get("selection"))
    
    st.session_state["interview"] = None
    st.session_state["created_interview_file"] = False
    st.session_state["feedback_string"] = None
    st.session_state["messages"] = []

    patient_name = st.selectbox("Which patient would you like to interview?", 
                                               ["John Smith", "Jackie Smith"],
                                               index = None,
                                               placeholder = "Select patient...")
    if patient_name: st.session_state["patient"] = GPT_Patient(patient_name)

    st.button("Start Interview", on_click=set_stage, args=[CHAT_SETUP])


if st.session_state["stage"] == CHAT_SETUP:
    llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model_name=MODEL, temperature=0.0)
    st.session_state["conversation"] = ConversationChain(llm=llm, memory=ConversationBufferMemory())
    initial_output = st.session_state["conversation"].predict(input = st.session_state["patient"].initial_input)

    st.session_state["messages"].append({"role": "Assistant", "content": "You may now begin your interview with " + st.session_state["patient"].name + "."})
    
    set_stage(CHAT_INTERFACE_TEXT)


if st.session_state["stage"] == CHAT_INTERFACE_TEXT:
    st.write(descriptions.get("interview"))
    
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input := st.chat_input("Type here..."):
        with st.chat_message(st.session_state["username"]):
            st.markdown(user_input)
        st.session_state["messages"].append({"role": st.session_state["username"], "content": user_input})
        output = st.session_state["conversation"].predict(input=user_input)
        with st.chat_message(st.session_state["patient"].name):
            st.markdown(output)
            st.session_state["messages"].append({"role": st.session_state["patient"].name, "content": output})

    st.button("End Interview", on_click=set_stage, args=[POST_INTERVIEW])


if st.session_state["stage"] == POST_INTERVIEW:
    st.write(descriptions.get("post"))
    
    if not st.session_state["created_interview_file"]:
        st.session_state["interview"] = methods.create_interview_file(st.session_state["username"], 
                                                                      st.session_state["patient"].name, 
                                                                      st.session_state["messages"])
        st.session_state["created_interview_file"] = True

    st.button("View Physical", on_click=set_stage, args=[PHYSICAL_SCREEN])
    st.button("View ECG", on_click=set_stage, args=[ECG_SCREEN])
    st.button("Provide Your Feedback", on_click=set_stage, args=[FEEDBACK_SCREEN])


if st.session_state["stage"] == PHYSICAL_SCREEN:
    st.header("Physical Examination Findings")
    st.write("Here is the full physical examination for " + st.session_state["patient"].name + ". Click the \"Back\" button to go back once you're done.")
    
    physical_exam_doc = Document(st.session_state["patient"].physical_path)
    for parargraph in physical_exam_doc.paragraphs:
        st.write(parargraph.text)
    
    st.button("Back", on_click=set_stage, args=[POST_INTERVIEW])
    

if st.session_state["stage"] == ECG_SCREEN:
    st.header("ECG Chart")
    st.write("Here is the ECG for " + st.session_state["patient"].name + ". Click the \"Back\" button to go back once you're done.")
    
    st.image(st.session_state["patient"].ECG_path)

    st.button("Back", on_click=set_stage, args=[POST_INTERVIEW])


if st.session_state["stage"]==FEEDBACK_SCREEN:
    st.write(descriptions.get("feedback"))
    st.session_state["diagnosis"]=st.text_area("Provide your differential diagnosis here:")
    st.session_state["feedback_string"] = st.text_area("Provide your feedback here:")

    st.button("Send", on_click=set_stage, args=[FINAL_SCREEN])
    st.button("Back", on_click=set_stage, args=[POST_INTERVIEW])
    
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    st.session_state["feedback_string"] = "<p> " + st.session_state["diagnosis"]+"</p> <p> "+st.session_state["feedback_string"]+" </p>"
    st.session_state["feedback_string"] = "<h2>User: "+st.session_state["username"]+ "</h2> <h3> Feedback: </h3>" + st.session_state["feedback_string"]


if st.session_state["stage"] == FINAL_SCREEN: 
    st.write(descriptions.get("final"))

    currentDateAndTime = date.datetime.now()
    date_time = currentDateAndTime.strftime("%d-%m-%y__%H-%M")

    # Setting up file for attachment sending
    bio = io.BytesIO()
    st.session_state["interview"].save(bio)
    methods.send_email(bio, EMAIL_TO_SEND, st.session_state["username"], date_time, st.session_state["feedback_string"])
    
    st.download_button("Download interview", 
                        data=bio.getvalue(),
                        file_name=st.session_state["username"]+"_"+date_time+".docx",
                        mime="docx")
    
    st.button("New Interview", on_click=set_stage, args=[SETTINGS])
    
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])