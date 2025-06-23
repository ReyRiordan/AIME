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
import emoji

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
@st.cache_resource
def init_connection():
    return MongoClient(DB_URI)

DB_CLIENT = init_connection()
COLLECTION_INTERVIEWS = DB_CLIENT["Benchmark"]["Interviews"]["M2_test"]
COLLECTION_EVALUATIONS = DB_CLIENT["Benchmark"]["Human_Eval"]["M2_test"]

def update_evaluation(checkpoint: str, evaluation: dict):
    """Update or insert an evaluation document in the database."""
    current_time = datetime.now().isoformat()
    evaluation['times'][current_time] = checkpoint
    query = {
        "username": st.session_state["username"],
        "interview_info._id": evaluation["interview_info"]["_id"]
    }
    COLLECTION_EVALUATIONS.replace_one(query, evaluation, upsert=True)

# OTHER
def load_and_setup():
    # Load the current interview based on view_index
    interview_id = st.session_state["interview_list"][st.session_state["current_index"]]["_id"]
    interview = COLLECTION_INTERVIEWS.find_one({"_id": interview_id})

    # Load or create the evaluation for this interview
    evaluation = COLLECTION_EVALUATIONS.find_one({"username": st.session_state["username"], "interview_info._id": interview_id})
    if not evaluation:
        evaluation = {
            "username": st.session_state["username"],
            "interview_info": st.session_state["interview_list"][st.session_state["current_index"]],
            "mark": "",
            "times": {}
        }
        # Initialize feedback structure
        feedback = {}
        for category, data in RUBRIC.items():
            if category in ["Assessment"]: # if multiple parts
                feedback[category] = {}
                for part in data:
                    feedback[category][part] = {"comment": None, "score": None}
            else:
                feedback[category] = {"comment": None, "score": None}
        evaluation["feedback"] = feedback

    # Insert if new, either way record start time
    if not st.session_state['started_time']:
        update_evaluation("start", evaluation)
        st.session_state['started_time'] = True

    return interview, evaluation


if st.session_state["stage"] == LOGIN_PAGE:
    layout1 = st.columns([2, 3, 2])
    with layout1[1]:
        st.title("MEWAI: Human Evaluation")
        st.write("Thank you so much for your cooperation.")
        st.write("Please begin by logging in as you were directed. If you encounter any issues, please contact rhr58@scarletmail.rutgers.edu")

        username = st.text_input("Username:")
        if username and username not in EVALUATORS: 
            st.write("Invalid username.")
        st.session_state["admin"] = True if username == "admin" else False
        password = st.text_input("Password:", type = "password")

        layout12b = layout1[1].columns(5)
        if layout12b[2].button("Log in"):
            if username in EVALUATORS:
                correct = EVALUATORS[username]["password"]
                if username in EVALUATORS and password == correct:
                    st.session_state["username"] = username
                    st.write("Authentication successful!")
                    time.sleep(1)
                    set_stage(HUMAN_EVAL)
                    st.rerun()
                else:
                    st.write("Password incorrect.")


if st.session_state["stage"] == HUMAN_EVAL:
    st.title("Human Evaluation")
    with st.expander("**Directions (click to expand)**"):
        st.write("For each section of the post note, the student's response is displayed on the right. Please carefully provide scores using the corresponding rubrics on the left side. Clicking to expand the \"Description\" will give you a detailed description of each section. In addition, at least one section has multiple parts - please provide a score for each part.")
        st.write("Use the \"Back\", \"Next\", and dropdown box to navigate freely between notes")
        st.write(emoji.emojize("Marking a note as done will mark it with a :white_check_mark: beside it in the dropdown. Flagging it will mark it with a :triangular_flag_on_post:."))
        st.write("Please note that you MUST press one of the buttons to save your progress (there is no auto-save), but all buttons including the dropdown selection will save.")
        st.write("NOTE: the comments/feedback section is optional!")
    layout1 = st.columns([2, 3, 2])

    # Update/initialize main lookup dict labels
    def update_label(evaluation, current_index):
        items = list(st.session_state["interviews_label:index"].items())
        for label, index in items:
            if index == current_index: 
                old_label = label
                break
        interview = evaluation["interview_info"]
        eval_for_label = COLLECTION_EVALUATIONS.find_one({"username": evaluation["username"], "interview_info._id": interview["_id"]})
        new_label = interview["netid"] + ": " + interview["patient"] + " " + eval_for_label["mark"]
        new_label = emoji.emojize(new_label, language='alias')
        reconstruct = {}
        for label, index in items:
            if label == old_label:
                reconstruct[new_label] = index
            else:
                reconstruct[label] = index
        st.session_state["interviews_label:index"] = reconstruct

    
    # Initialize data if needed
    if "interview_list" not in st.session_state:
        st.session_state["interview_list"] = list(COLLECTION_INTERVIEWS.find({}, {"netid": 1, "patient": 1}))
        st.session_state["interviews_label:index"] = {}
        for index, interview in enumerate(st.session_state["interview_list"]):
            label = interview["netid"] + ": " + interview["patient"]
            eval_for_label = COLLECTION_EVALUATIONS.find_one({"username": st.session_state["username"], "interview_info._id": interview["_id"]})
            if eval_for_label:
                label += " " + eval_for_label["mark"]
                label = emoji.emojize(label, language='alias')
            st.session_state["interviews_label:index"][label] = index
        st.session_state["current_index"] = None
        st.session_state["current_evaluation"] = None
        st.session_state['started_time'] = False

    # Selectbox section
    layout11 = layout1[1].columns([1, 2, 1])
    
    # Function for selectbox change
    def on_select_change():
        if st.session_state["current_evaluation"]:
            update_evaluation("end", st.session_state["current_evaluation"])
        # Get the new index from the selected label
        st.session_state["current_index"] = st.session_state["interviews_label:index"][st.session_state["selected"]]
        st.session_state['started_time'] = False
        
    # Create the selectbox
    # selectbox_index = st.session_state.get("current_index", None)
    # previous = st.session_state.get("selected", None)
    layout11[1].selectbox(
        "Select an interview:", 
        options=st.session_state["interviews_label:index"],
        index=st.session_state["current_index"],
        placeholder="Select Interview", 
        label_visibility="collapsed", 
        key="selected",
        on_change=on_select_change
    )
    # # If the user changed the selection, update evaluation
    # if previous and selected != previous:
    #     update_evaluation("end", st.session_state["current_evaluation"])
    #     st.session_state["current_index"] = st.session_state["interviews_label:index"][selected]

    if st.session_state["current_index"] is not None:
        # Load/setup current interview and evaluation as needed
        interview, evaluation = load_and_setup()
        st.session_state["current_evaluation"] = evaluation
        # Display the evaluation form and capture updated feedback
        evaluation["feedback"] = display_evaluation(interview, evaluation["feedback"])
        st.session_state["current_evaluation"] = evaluation

    # Function to handle dropdown navigation
    def navigate(direction):
        update_evaluation("end", st.session_state["current_evaluation"])
        
        # Update the view index based on direction
        if direction == "next":
            st.session_state["current_index"] = min(len(st.session_state["interview_list"]) - 1, 
                                              st.session_state["current_index"] + 1)
        elif direction == "back":
            st.session_state["current_index"] = max(0, st.session_state["current_index"] - 1)

        st.session_state['started_time'] = False

    # Function to mark current evaluation
    def mark_evaluation(mark: str):
        st.session_state["current_evaluation"]["mark"] = mark
        update_evaluation("mark", st.session_state["current_evaluation"])
        update_label(st.session_state["current_evaluation"], st.session_state["current_index"])

    # Function to save current evaluation
    def save_evaluation():
        update_evaluation("save", st.session_state["current_evaluation"])
        
    if st.session_state["current_index"] is not None:
        # Top navigation buttons
        if layout11[0].button("Back", use_container_width=True, key="backtop"):
            navigate("back")
            st.rerun()
        if layout11[2].button("Next", use_container_width=True, key="nexttop"):
            navigate("next")
            st.rerun()
        
        # Save button
        layout12 = layout1[1].columns([1, 1, 1])
        if layout12[0].button(emoji.emojize("Flag :triangular_flag_on_post:"), use_container_width=True, key="flagtop"):
            mark_evaluation(":triangular_flag_on_post:")
            st.rerun()
        if layout12[1].button("Save", use_container_width=True, key="savetop"):
            save_evaluation()
            st.rerun()
        if layout12[2].button(emoji.emojize("Done :white_check_mark:"), use_container_width=True, key="donetop"):
            mark_evaluation(":white_check_mark:")
            st.rerun()

    # # Bottom navigation buttons
    # layout2 = st.columns([2, 3, 2])
    # layout21 = layout2[1].columns([1, 1, 1])
    # if layout21[0].button(emoji.emojize("Flag :triangular_flag_on_post:", language="alias"), use_container_width=True, key="flagbot"):
    #     mark_evaluation(":triangular_flag_on_post:")
    #     st.rerun()
    # if layout21[1].button("Save", use_container_width=True, key="savebot"):
    #     save_evaluation()
    #     st.rerun()
    # if layout21[2].button(emoji.emojize("Done :white_check_mark:"), use_container_width=True, key="donebot"):
    #     mark_evaluation(":white_check_mark:")
    #     st.rerun()
    # layout22 = layout2[1].columns([1, 2, 2, 1])
    # if layout22[1].button("Back", use_container_width=True, key="backbot"):
    #     navigate("back")
    #     st.rerun()
    # if layout22[2].button("Next", use_container_width=True, key="nextbot"):
    #     navigate("next")
    #     st.rerun()