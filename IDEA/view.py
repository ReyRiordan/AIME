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


# STREAMLIT SETUP
st.set_page_config(page_title = "AIME",
                   page_icon = "🧑‍⚕️",
                   layout = "wide",
                   initial_sidebar_state="collapsed")

if "stage" not in st.session_state:
    st.session_state["stage"] = LOGIN_PAGE

def set_stage(stage):
    st.session_state["stage"] = stage


# DB SETUP
@st.cache_resource
def init_connection():
    return MongoClient(DB_URI)

DB_CLIENT = init_connection()
COLLECTION = DB_CLIENT[DB_NAME]["Interviews"]

@st.cache_data(ttl=600)
def get_data():
    DB = DB_CLIENT[DB_NAME]
    items = DB["Interviews"].find()
    items = list(items)  # make hashable for st.cache_data
    return items


if st.session_state["stage"] == LOGIN_PAGE:
    layout1 = st.columns([2, 3, 2])
    with layout1[1]:
        st.title("View Interviews")
        st.write("Welcome! This is a small branch site where you can view the interviews and feedback you have recorded on the main site.")
        st.write("Begin by logging in as directed. If you encounter any issues, please contact rhr58@scarletmail.rutgers.edu")

        username = st.text_input("Username (NetID):")
        if username and username not in ASSIGNMENTS: 
            st.write("Invalid username.")
        password = st.text_input("Password (LastFirst, can also just use NetID if not working):", type = "password")

        # ADMIN
        st.session_state["admin"] = True if username == "admin" else False

        layout12b = layout1[1].columns(5)
        if layout12b[2].button("Log in"):
            correct = ASSIGNMENTS[username]["Last_name"] + ASSIGNMENTS[username]["First_name"]
            if username in ASSIGNMENTS and (password == correct or password == username):
                st.session_state["username"] = username
                st.session_state["assignment"] = ASSIGNMENTS[username]
                st.write("Authentication successful!")
                time.sleep(1)
                set_stage(VIEW_INTERVIEWS)
                st.rerun()
            else:
                st.write("Password incorect.")