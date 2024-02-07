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
from virtual_patient.patients import GPT_patient
from annotated_text import annotated_text

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
st.title("Feedback Screen (ALPHA)")

st.session_state["messages"] = [{"role" : "User", "content" : "Hi there, I'm Dr. Corbett. What brings you in today?"},
                                {"role" : "John Smith", "content" : "I'm old."}]

chat_container = st.container(height=300)
for message in st.session_state["messages"]:
        with chat_container:
            with st.chat_message(message["role"]):
                annotated_text((message["content"], "Introduction, Establish Chief Concern", "#bae1ff"))

st.session_state["general_classed"] = {"Introduction" : True,
                                    "Confirm_Identity" : False,
                                    "Establish_Chief_Concern" : True,
                                    "Additional_Information" : False,
                                    "Medical_History" : False,
                                    "Surgery_Hospitalization" : False,
                                    "Medication" : False,
                                    "Allergies" : False,
                                    "Family_History" : False,
                                    "Alcohol" : False,
                                    "Smoking" : False,
                                    "Drug_Use" : False}
st.session_state["dims_classed"] = {"Onset" : True,
                                    "Quality" : False,
                                    "Location" : False,
                                    "Timing" : False,
                                    "Pattern" : True,
                                    "Exacerbating" : True,
                                    "Relieving" : True,
                                    "Prior_History" : False,
                                    "Radiation" : False,
                                    "Severity" : False}

general_score = 0
for label in st.session_state["general_classed"]:
     if st.session_state["general_classed"][label] == True:
          general_score += 1

st.header(":blue[General Questions]: " + str(general_score) + "/" + str(len(st.session_state["general_classed"])), divider = "blue")
general_display = []
for key, value in st.session_state["general_classed"].items():
     general_display.append((key.replace("_", " "), "", "#baffc9" if value else "#ffb3ba"))
annotated_text(general_display)

dims_score = 0
for label in st.session_state["dims_classed"]:
     if st.session_state["dims_classed"][label] == True:
          dims_score += 1

st.header(":red[Dimensions of Chief Concern]: " + str(dims_score) + "/" + str(len(st.session_state["dims_classed"])), divider = "red")
dims_display = []
for key, value in st.session_state["dims_classed"].items():
     dims_display.append((key.replace("_", " "), "", "#baffc9" if value else "#ffb3ba"))
annotated_text(dims_display)