from openai import OpenAI
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
import tempfile
from annotated_text import annotated_text
# from dotenv import load_dotenv

# load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
st.session_state["username"] = "TESTING"
st.title("Medical Interview Simulation (CONVO ONLY)")

if "stage" not in st.session_state:
    st.session_state["stage"] = SETTINGS

def set_stage(stage):
    st.session_state["stage"] = stage

if st.session_state["stage"] == SETTINGS:
    st.session_state["interview"] = None
    st.session_state["chatbot"] = None
    st.session_state["convo_memory"] = None
    st.session_state["convo_file"] = None
    patient_name = st.selectbox("Which patient would you like to interview?", 
                                                ["John Smith", "Jackie Smith"],
                                                index = None,
                                                placeholder = "Select patient...")
    if patient_name: st.session_state["interview"] = Interview(st.session_state["username"], Patient(patient_name))

    st.button("Start Interview", on_click=set_stage, args=[CHAT_SETUP])


if st.session_state["stage"] == CHAT_SETUP:
    st.session_state["chatbot"] = OpenAI()
    st.session_state["convo_memory"] = [{"role": "system", "content": st.session_state["interview"].get_patient().convo_prompt}]

    st.session_state["interview"].add_message(Message("N/A", "Assistant", "You may now begin your interview with " + st.session_state["interview"].get_patient().name + ". Start by introducing yourself."))
    
    set_stage(CHAT_INTERFACE_VOICE)


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
        st.session_state["convo_memory"].append({"role": "user", "content": user_input})
        response = st.session_state["chatbot"].chat.completions.create(model = CONVO_MODEL, temperature = 0.0, messages = st.session_state["convo_memory"])
        output = response.choices[0].message.content
        with container:
            with st.chat_message("AI"): # Needs avatar eventually
                st.markdown(output)
        st.session_state["interview"].add_message(Message("output", "AI", output))
        st.session_state["convo_memory"].append({"role": "assistant", "content": output})

    columns = st.columns(4)
    columns[1].button("Restart", on_click=set_stage, args=[SETTINGS])
    columns[2].button("End Interview", on_click=set_stage, args=[DIAGNOSIS])

if st.session_state["stage"] == DIAGNOSIS:
    st.download_button("Download JSON",
                    data=json.dumps(st.session_state["interview"].get_dict(),indent=4),
                    file_name = st.session_state["interview"].get_username() + "_" + ".json",
                    mime="json")

