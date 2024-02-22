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
from dotenv import load_dotenv

load_dotenv()

st.title("Medical Interview Simulation (BETA)")

st.session_state["interview"]=Interview("Rey Riordan",Patient("Jackie Smith"))

st.session_state["interview"].add_message(Message("N/A", "Assistant", "You may now begin your interview with " + st.session_state["interview"].get_patient().name + ". Start by introducing yourself."))

st.session_state["interview"].add_message(Message("N/A", "Assistant", "You may now begin your interview with " + st.session_state["interview"].get_patient().name + ". Start by introducing yourself."))

st.session_state["interview"].add_message(Message("input", "User", "mofo when you gonna die?"))

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


st.download_button("Download JSON",
                data=json.dumps(st.session_state["interview"].get_dict(),indent=4),
                file_name = st.session_state["interview"].get_username() + "_" + ".json",
                mime="json")

