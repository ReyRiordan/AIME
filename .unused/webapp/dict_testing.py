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

client = MongoClient(DB_URI,server_api=ServerApi('1'))

# Ping server on startup

try:
    client.admin.command('ping')
    print("Connection Successful")
except Exception as e:
    print(e)

# Method to get data of server

@st.cache_data(ttl=1200)
def get_data():
    db=client["AIME"]
    items=db["Conversation"].find()
    items = list(items)
    return items

# MongoDB Collection to add to

collection=client["AIME"]["Conversation"]


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

    st.json(st.session_state["interview"].model_dump())



