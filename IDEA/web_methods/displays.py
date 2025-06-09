from docx import Document
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName,
    FileType, Disposition, ContentId)
import os
import datetime as date
import base64
import io
import streamlit as st
from audiorecorder import audiorecorder
from openai import OpenAI
from annotated_text import annotated_text
import json
import tempfile
from web_classes import *
from typing import List
from lookups import *


def display_evaluation(interview: dict, user_inputs: dict) -> dict:
    student_responses = interview["post_note"]
    categories = []
    for cat, input in student_responses.items():
        if input: categories.append(cat)
    for category in categories:
        response = student_responses[category]
        with st.container(border = True):
            st.header(f"{category}", divider = "grey")
            layout1 = st.columns([1, 1])
            with layout1[0]:
                st.subheader("**Student response:**")
                st.write(student_responses[category])
            with layout1[1]:
                st.subheader("**Evaluation:**")
                if category in ["Assessment"]: # if multiple parts
                    st.write(":exclamation: Please make sure to do each part by switching between the 3 tabs! :exclamation:")
                    parts = [part for part in RUBRIC[category]]
                    tabs = st.tabs(parts)
                    for i, part in enumerate(parts):
                        with tabs[i]:
                            comment_key = f"{interview['_id']}_{category}_{part}_comment"
                            score_key = f"{interview['_id']}_{category}_{part}_score"
                            user_inputs[category][part]["comment"] = st.text_area("Comments/feedback: ", 
                                                                                  key = comment_key, 
                                                                                  value = user_inputs[category][part]["comment"])
                            layout11 = st.columns([1, 5])
                            user_inputs[category][part]["score"] = layout11[0].text_input(f"Score (out of **{RUBRIC[category][part]['points']}**): ", 
                                                                                          key = score_key, 
                                                                                          value = user_inputs[category][part]["score"])
                            with st.container(border=True):
                                st.write("**Rubric:**")
                                st.html(RUBRIC[category][part]["html"])
                                with st.expander("Description"):
                                    st.write(RUBRIC[category][part]["title"] + ": " + RUBRIC[category][part]["desc"])
                else:
                    comment_key = f"{interview['_id']}_{category}_comment"
                    score_key = f"{interview['_id']}_{category}_score"
                    user_inputs[category]["comment"] = st.text_area("Comments/feedback: ", 
                                                                    key = comment_key, 
                                                                    value = user_inputs[category]["comment"])
                    layout11 = st.columns([1, 5])
                    user_inputs[category]["score"] = layout11[0].text_input(f"Score (out of **{RUBRIC[category]['points']}**): ", 
                                                                            key = score_key, 
                                                                            value = user_inputs[category]["score"])
                    with st.container(border=True):
                        st.write("**Rubric:**")
                        st.html(RUBRIC[category]["html"])
                        with st.expander("Description"):
                            st.write(RUBRIC[category]["title"] + ": " + RUBRIC[category]["desc"])
        
    return user_inputs

        


def display_PostNote(feedback: dict, inputs: dict, short: bool) -> None:
    # print(feedback)
    inst = st.session_state["admin"]
    for category, d in feedback["feedback"].items():
        if short and category in ["Key Findings", "HPI", "Past Histories"]: continue
        with st.container(border = True):
            st.header(f"{category}", divider = "grey")
            layout1 = st.columns([1, 1])
            with layout1[0]:
                st.subheader("**Your answer:**")
                st.write(inputs[category])
            with layout1[1]:
                st.subheader("**Feedback:**")
                if category in ["HPI", "Past Histories", "Assessment"]:
                    st.write("Make sure to check each section!")
                    parts = [part for part in d]
                    tabs = st.tabs(parts)
                    for i, part in enumerate(parts):
                        dd = d[part]
                        with tabs[i]:
                            if inst: st.write(f"**Score: {dd['score']}/{dd['max']}**")
                            st.write(dd["comment"])
                            with st.expander("Rubric"):
                                st.write(dd["desc"])
                                st.html(dd["html"])
                            if inst:
                                with st.expander("Thought process"):
                                    if dd["thought"]: st.write(dd["thought"])
                            st.divider()
                else:
                    if inst: st.write(f"**Score: {d['score']}/{d['max']}**")
                    st.write(d["comment"])
                    with st.expander("Rubric"):
                        st.write(d["desc"])
                        st.html(d["html"])
                    if inst:
                        with st.expander("Thought process"):
                            if d["thought"]: st.write(d["thought"])


def display_Interview(interview: dict) -> None:
    # st.write(f"User: {interview['username']}, Patient: {interview['patient']['id']}")
    # if 'start_time' in interview and interview['start_time']:
    #     st.write(f"Start Time: {interview['start_time']}")
    # if 'time_elapsed' in interview and interview['time_elapsed']:
    #     st.write(f"Time Elapsed: {interview['time_elapsed']}")
    # if 'date_time' in interview and interview['date_time']:
    #     st.write(f"Time: {interview['date_time']}")
    # if 'cost' in interview and interview['cost']:
    #     st.write(f"Estimated Cost: ${interview['cost']}")

    # print(interview)
    post_note, transcript, explanation = st.tabs(["Post Note", "Interview Transcript", "Case Explanation"])
    
    if interview["feedback"]:
        with post_note:
            if not interview["post_note_inputs"]["HPI"]: short = True
            display_PostNote(interview["feedback"], interview["post_note_inputs"], short=short)
    
    with transcript:
        chat_container = st.container(height=700)
        for message in interview["messages"]:
            with chat_container:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
    
    with explanation:
        explanation_file = interview["patient"]["explanation"]
        with open(explanation_file, "rb") as pdf_file:
            explanation = pdf_file.read()
            st.download_button("Download Case Explanation (PDF)", explanation, explanation_file)

        # if interview["diagnosis_inputs"]:
        #     diagnosis_inputs = interview["diagnosis_inputs"]
        #     st.divider()
        #     st.write("Interpretative Summary: " + diagnosis_inputs["Summary"])
        #     st.write("Potential Diagnoses: " + ", ".join(diagnosis_inputs["Potential"]))
        #     st.write("Rationale: " + diagnosis_inputs["Rationale"])
        #     st.write("Final Diagnosis: " + diagnosis_inputs["Final"])
