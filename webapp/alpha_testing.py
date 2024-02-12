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
from website_classes import *


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
st.title("Feedback (ALPHA)")


st.session_state["patient"] = GPT_Patient("John Smith")
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

st.session_state["messages"] = []
for message in messages:
     if message["role"] == "User":
          st.session_state["messages"].append(Message("input", message["role"], message["content"]))
     elif message["role"] == "AI":
          st.session_state["messages"].append(Message("output", message["role"], message["content"]))

# for message in st.session_state["messages"]:
#      st.write(message.content)


methods.annotate(st.session_state["patient"], st.session_state["messages"], OPENAI_API_KEY)
st.session_state["grades"], st.session_state["scores"] = methods.grade_data_acquisition(st.session_state["patient"], st.session_state["messages"])

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

    def display_section(header_text, scores, grades, color):
        score, score_max = scores
        st.header(f":{color}[{header_text}]: {score}/{score_max}", divider=color)
        display_data = [(key.replace("_", " "), "", "#baffc9" if value else "#ffb3ba") for key, value in grades.items()]
        annotated_text(display_data)

    display_section("General Questions", st.session_state["scores"]["gen"], st.session_state["grades"]["gen"], "blue")
    display_section("Dimensions of Chief Concern", st.session_state["scores"]["dims"], st.session_state["grades"]["dims"], "red")
    display_section("Associated Symptom Questions", st.session_state["scores"]["asoc"], st.session_state["grades"]["asoc"], "orange")
    display_section("Risk Factor Questions", st.session_state["scores"]["risk"], st.session_state["grades"]["risk"], "violet")