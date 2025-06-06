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
import statistics


# STREAMLIT SETUP
st.set_page_config(page_title = "MEWAI",
                   page_icon = "🧑‍⚕️",
                   layout = "wide",
                   initial_sidebar_state="collapsed")

if "stage" not in st.session_state:
    st.session_state["stage"] = LOGIN_PAGE

def set_stage(stage):
    st.session_state["stage"] = stage


# DB SETUP
DB_CLIENT = init_connection()
DB_NAME = "M2"
COLLECTION = DB_CLIENT[DB_NAME]["Interviews"]

@st.cache_data(ttl=600)
def get_data(username: str = None) -> list[dict]:
    DB = DB_CLIENT[DB_NAME]
    items = DB["Interviews"].find()
    items = list(items)  # make hashable for st.cache_data

    if username:
        only_user = []
        for item in items:
            if item["username"] == username: only_user.append(item)
        items = only_user
    
    items = sorted(items, key=lambda x: datetime.fromisoformat(x["start_time"]), reverse=True)
    return items

# @st.cache_data(ttl=600)
# def get_data(username: str = None) -> list[dict]:
#     DB = DB_CLIENT[DB_NAME]
#     query = {"username": username} if username else {}
#     return list(DB["Interviews"].find(query).sort("start_time", -1))


# MISC
def read_time(iso_time) -> str:
    if not iso_time: return "N/A"
    dt = datetime.fromisoformat(iso_time)
    est = pytz.timezone("US/Eastern")
    dt_est = dt.astimezone(est)
    return dt_est.strftime("%B %d, %Y at %I:%M %p")


if st.session_state["stage"] == LOGIN_PAGE:
    layout1 = st.columns([2, 3, 2])
    with layout1[1]:
        st.title("View Interviews")
        st.write("Welcome! This is a small branch site where you can view the interviews and feedback you have recorded on the main site.")
        st.write("Begin by logging in as directed. If you encounter any issues, please contact rhr58@scarletmail.rutgers.edu")

        username = st.text_input("Username (NetID):")
        if username and username not in ASSIGNMENTS: 
            st.write("Invalid username.")
        password = st.text_input("Password (FirstLast):", type = "password")

        # ADMIN
        st.session_state["admin"] = True if username == "admin" else False

        layout12b = layout1[1].columns(5)
        if layout12b[2].button("Log in"):
            correct = ASSIGNMENTS[username]["First_name"] + ASSIGNMENTS[username]["Last_name"]
            if username in ASSIGNMENTS and (password == correct or password == username):
                st.session_state["username"] = username
                st.session_state["assignment"] = ASSIGNMENTS[username]
                st.write("Authentication successful!")
                time.sleep(1)
                next = VIEW_INTERVIEWS_ADMIN if st.session_state["admin"] else VIEW_INTERVIEWS
                set_stage(next)
                st.rerun()
            else:
                st.write("Password incorect.")


if st.session_state["stage"] == VIEW_INTERVIEWS_ADMIN:
    DATA = get_data()

    st.title("ADMIN VIEW")
    view_tab, stats_tab, surveys_tab = st.tabs(["View", "Stats", "Surveys"])


    with view_tab:
        ##### SELECTION #####
        if "view_index" not in st.session_state:
            st.session_state["view_index"] = 0
        
        interview_list = {}
        for i in range(len(DATA)):
            interview = DATA[i]
            label = interview["username"] + ": " + interview["patient"]["id"] + " @ " + read_time(interview["start_time"])
            interview_list[label] = i

        selected = st.selectbox("Select an interview:", 
                                options = interview_list, 
                                placeholder = "Select Interview")
        st.session_state["view_index"] = interview_list[selected]

        st.divider()

        ##### VIEW ######
        CURRENT = DATA[st.session_state["view_index"]]

        st.write(f"START: {read_time(CURRENT['start_time'])}")
        # st.write(f"START: {read_time(CURRENT['start_time'])} / END: {read_time(CURRENT['end_time'])}")
        # if CURRENT["end_time"]:
        #     duration = datetime.fromisoformat(CURRENT["end_time"]) - datetime.fromisoformat(CURRENT["start_time"])
        #     st.write(f"Duration: {duration.total_seconds() // 60} min")
        st.write(f"Patient: {CURRENT['patient']['id']} ({CURRENT['chat_mode']})")

        st.subheader("Transcript")
        if CURRENT["messages"]:
            chat_container = st.container(height=700)
            for message in CURRENT["messages"]:
                with chat_container:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])
        else:
            st.write("N/A")

        st.divider()

        st.subheader("Feedback")
        if CURRENT["feedback"]: 
            display_PostNote(CURRENT["feedback"], CURRENT["post_note_inputs"], short = True)
        else: 
            st.write("N/A")

        st.divider()

        st.subheader("Survey")
        if CURRENT["survey"]: 
            st.write(CURRENT["survey"])
        else: 
            st.write("N/A")


    with stats_tab:
        # st.write("Total number of M1 students: 172 (108 F, 64 M)")
        st.write(f"Total interviews: {len(DATA)}")

        counts = {}
        durations = []
        for interview in DATA:
            if interview["username"] not in counts:
                counts[interview["username"]] = 1
            else: counts[interview["username"]] += 1
            # if interview["end_time"]:
            #     duration = datetime.fromisoformat(interview["end_time"]) - datetime.fromisoformat(interview["start_time"])
            #     durations.append(duration.total_seconds())
        st.write(f"Number of unique students who participated: {len(counts)}")
        # st.write(f"Durations: mean {statistics.mean(durations) // 60} min, median {statistics.median(durations) // 60} min, stdev {statistics.stdev(durations) // 60} min")

        slackers = []
        for username in ASSIGNMENTS:
            if username not in counts and username not in ["rhr58", "admin"]: slackers.append(username)
        overachievers = {}
        for user in counts:
            if counts[user] > 2: overachievers[user] = counts[user]
        overachievers = dict(sorted(overachievers.items(), key=lambda x: x[1], reverse=True))
        st.write(f"Students who didn't participate: {slackers}")
        st.write(f"Students who did more than 2 interviews: {overachievers}")

        # st.write("Total cost $51.21 -> ~11.6 cents per interview, of which ~75% used for interview")


    with surveys_tab:
        surveys = []
        for interview in DATA:
            if interview["survey"]: surveys.append(interview["survey"])
        for survey in surveys:
            st.write(survey)


if st.session_state["stage"] == VIEW_INTERVIEWS:
    DATA = get_data(st.session_state["username"])
    
    st.title(f"View Interviews for {st.session_state['username']}")

    