import time
from datetime import datetime
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
import pytz

# STREAMLIT SETUP
st.set_page_config(page_title = "MEWAI",
                   page_icon = "🧑‍⚕️",
                   layout = "wide",
                   initial_sidebar_state="collapsed")

if "stage" not in st.session_state:
    st.session_state["stage"] = CLOSED

def set_stage(stage):
    st.session_state["stage"] = stage


# DB SETUP
@st.cache_resource
def init_connection():
    return MongoClient(DB_URI)

DB_CLIENT = init_connection()
COLLECTION = DB_CLIENT[DB_NAME]["Interviews"]

def insert_eval(EVAL):
    COLLECTION.insert_one(EVAL)

def update_eval(EVAL):
    COLLECTION.replace_one({"username" : EVAL["username"], 
                            "netid": EVAL["netid"],
                            "start_time": EVAL["start_time"]}, 
                            EVAL)

def get_interview(netid: str, start_time: str) -> dict | None:
    DB = DB_CLIENT[DB_NAME]
    query = {
        "netid": netid,
        "start_time": start_time
    }
    return DB["Interviews"].find_one(query)


if st.session_state["stage"] == LOGIN_PAGE:
    layout1 = st.columns([2, 3, 2])
    with layout1[1]:
        st.title("MEWAI: Human Evaluation")
        st.write("Thank you so much for your cooperation.")
        st.write("Please begin by logging in as you were directed. If you encounter any issues, please contact rhr58@scarletmail.rutgers.edu")

        username = st.text_input("Username:")
        if username and username not in EVALS: 
            st.write("Invalid username.")
        st.session_state["admin"] = True if username == "admin" else False
        password = st.text_input("Password:", type = "password")

        layout12b = layout1[1].columns(5)
        if layout12b[2].button("Log in"):
            if username in EVALS:
                correct = EVALS[username]["password"]
                if username in EVALS and password == correct:
                    st.session_state["username"] = username
                    st.write("Authentication successful!")
                    time.sleep(1)
                    set_stage(HUMAN_EVAL)
                    st.rerun()
                else:
                    st.write("Password incorrect.")


if st.session_state["stage"] == HUMAN_EVAL:
    st.title("Human Evaluation")
    layout1 = st.columns([3, 1])
    layout1[0].write("For each section of the post note, the student's response is displayed on the right. Please carefully provide scores using the corresponding rubrics on the left side.")
    layout1[0].write("Note that the rubrics start out hidden for each section; please click on the dropdown to display. In addition, some sections have multiple parts/tabs - please provide a score for each one.")
    layout11 = layout1[1].columns([1, 2, 1])
    layout11[1].button("**Next**", on_click=set_stage, args=[SURVEY], use_container_width=True, key=1)
    
    # Let the display methods cook
    display_Interview(st.session_state["interview"].model_dump())

    st.divider()
    layout2 = st.columns([1, 2, 1])
    layout2[1].button("**Next**", on_click=set_stage, args=[SURVEY], use_container_width=True, key=2)