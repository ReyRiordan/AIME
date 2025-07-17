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
import string
import pandas as pd


def display_evaluation(interview: dict, user_inputs: dict) -> dict:
    student_responses = interview["post_note_inputs"]
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
                            feature_key = f"{interview['_id']}_{category}_{part}_feature"
                            user_inputs[category][part]["comment"] = st.text_area("Comments/feedback: ", 
                                                                                  key = comment_key, 
                                                                                  value = user_inputs[category][part]["comment"])
                            features = user_inputs[category][part]['features']
                            layout11 = st.columns([1 for i in range(10)])
                            for i, (key, value) in enumerate(features.items()):
                                features[key] = layout11[i].checkbox(key,
                                                                     key = feature_key+str(i),
                                                                     value = value)
                            layout12 = st.columns([1, 5])
                            user_inputs[category][part]["score"] = layout12[0].text_input(f"Score (out of **{RUBRIC[category][part]['points']}**): ", 
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
                    feature_key = f"{interview['_id']}_{category}_feature"
                    user_inputs[category]["comment"] = st.text_area("Comments/feedback: ", 
                                                                    key = comment_key, 
                                                                    value = user_inputs[category]["comment"])
                    features = user_inputs[category]['features']
                    layout11 = st.columns([1 for i in range(10)])
                    for i, (key, value) in enumerate(features.items()):
                        features[key] = layout11[i].checkbox(key,
                                                             key = feature_key+str(i),
                                                             value = value)
                    layout12 = st.columns([1, 5])
                    user_inputs[category]["score"] = layout12[0].text_input(f"Score (out of **{RUBRIC[category]['points']}**): ", 
                                                                            key = score_key, 
                                                                            value = user_inputs[category]["score"])
                    with st.container(border=True):
                        st.write("**Rubric:**")
                        st.html(RUBRIC[category]["html"])
                        with st.expander("Description"):
                            st.write(RUBRIC[category]["title"] + ": " + RUBRIC[category]["desc"])
        
    return user_inputs


def display_section(interview: dict, inputs: dict, rubric: dict) -> None:
    st.write(inputs["comment"])
    for i, (key, value) in enumerate(inputs['features'].items()):
        st.write(f"{value}")
    st.write(inputs["score"])

def display_comparison(interview: dict, evaluations: list[dict]) -> None:
    student_responses = interview["post_note_inputs"]
    categories = []
    for cat, input in student_responses.items():
        if input: categories.append(cat)

    for category in categories:
        response = student_responses[category]
        with st.container(border = True):
            st.header(f"{category}", divider = "grey")
            layout1 = st.columns([1, 2])

            with layout1[0]:
                st.subheader("**Student response:**")
                st.write(student_responses[category])

            with layout1[1]:
                st.subheader("**Evaluations:**")
                evalers = list(evaluations.keys())

                if category in ["Assessment"]: # if multiple parts
                    parts = [part for part in RUBRIC[category]]
                    tabs = st.tabs(parts)
                    for i, part in enumerate(parts):
                        with tabs[i]:
                            layout11 = st.columns([1 for i in range(len(evalers))])
                            rubric = RUBRIC[category][part]
                            for evaler_index in range(len(evalers)):
                                evaler = evalers[evaler_index]
                                if evaluations[evaler]:
                                    evaler_inputs = evaluations[evaler]['feedback'][category][part]
                                    with layout11[evaler_index]:
                                        display_section(interview, evaler_inputs, rubric)
                            with st.container(border=True):
                                st.write("**Rubric:**")
                                st.html(rubric["html"])
                                with st.expander("Description"):
                                    st.write(rubric["title"] + ": " + rubric["desc"])
                else:
                    layout11 = st.columns([1] + [2 for i in range(len(evalers))])
                    rubric = RUBRIC[category]
                    to_df = {'evaler': [],
                             'score': []}
                    for i in range(rubric['features']):
                        to_df[string.ascii_lowercase[i]] = []
                    to_df['comment'] = []
                    for evaler in evalers:
                        to_df['evaler'].append(evaler)
                        if evaluations[evaler]:
                            inputs = evaluations[evaler]['feedback'][category]
                            for key, value in inputs.items():
                                if key == 'features':
                                    for k, v in inputs['features'].items(): 
                                        to_df[k].append(v)
                                else:
                                    to_df[key].append(value)
                        else:
                            for key, value in to_df.items():
                                if key != 'evaler': to_df[key].append(None)
                    df = pd.DataFrame(to_df)
                    config = {
                        'evaler': st.column_config.Column("Evaluator", width="small", pinned=True),
                        'score': st.column_config.Column(f"Score / {rubric['points']}", width="small"),
                        'comment': st.column_config.Column(f"Comment", width="large")
                    }
                    st.dataframe(df, column_config=config, hide_index=True, use_container_width=True)
                    with st.container(border=True):
                        st.write("**Rubric:**")
                        st.html(rubric["html"])
                        with st.expander("Description"):
                            st.write(rubric["title"] + ": " + rubric["desc"])


def display_PostNote(feedback: dict, inputs: dict) -> None:
    # print(feedback)
    inst = st.session_state["admin"]
    for category, d in feedback["post_note"].items():
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
                                st.write(RUBRIC[category][part]["desc"])
                                st.html(RUBRIC[category][part]["html"])
                            if inst:
                                with st.expander("Thought process"):
                                    if dd["thought"]: st.write(dd["thought"])
                            st.divider()
                else:
                    if inst: st.write(f"**Score: {d['score']}/{d['max']}**")
                    st.write(d["comment"])
                    with st.expander("Rubric"):
                        st.write(RUBRIC[category]["desc"])
                        st.html(RUBRIC[category]["html"])
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
            display_PostNote(interview["feedback"], interview["post_note_inputs"])
    
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
