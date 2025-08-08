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


def auto_score(part: str, features: dict[str, bool]) -> int:
    num_present = 0
    for f in features:
        if features[f]: num_present += 1

    if part == "Summary Statement":
        if features['A']:
            if num_present == 7: return 4
            elif num_present >= 5 and features['G']: return 3
            elif num_present >= 3: return 2
            elif num_present >= 2: return 1
            else: return 0
        else:
            return 0
    elif part == "Differential Diagnosis":
        if features['A'] and features['B'] and features['C'] and features['D']: return 2
        elif features['A'] and num_present >= 2: return 1
        else: return 0
    elif part == "Explanation of Lead Diagnosis":
        if num_present >= 3: return 2
        elif features['A'] and num_present >= 2: return 1
        else: return 0
    elif part == "Explanation of Alternative Diagnoses":
        if num_present >= 3: return 2
        elif features['A'] and num_present >= 2: return 1
        else: return 0
    elif part == "Plan":
        if num_present >= 5: return 3
        elif features['A'] and ((features['B'] and features['D']) or (features['C'] and features['E'])): return 2
        else: return 1

def display_part(eval: dict, section: str, part: str, sim_id: str) -> None:
        values = eval[section][part]
        rubric = RUBRIC[section][part]
        prefix = f"{sim_id}_{part}" # Use sim_id to make keys unique across simulations

        score_placeholder = st.empty()
        
        features = values['features']
        for i, (key, value) in enumerate(features.items()):
            label = f"**{key}**: {rubric['features'][key]}"
            features[key] = st.checkbox(label,
                                        key = f"{prefix}_feature_{key}"+str(i),
                                        value = value)
        
        values["comment"] = st.text_area("**Comments** (detailed rationale, as if it's a real clerkship OSCE post note review):", 
                                        key = f"{prefix}_comment", 
                                        value = values["comment"])
        
        score = auto_score(part, features)
        values["score"] = score
        with score_placeholder:
            st.html(f"<span style=\"font-size: larger;\"><b>Score: {score}/{next(iter(rubric['points']))}</b></span>")

def display_evaluation(interview: dict, evaluation: dict) -> dict:
    sim_id = str(interview["_id"])  # Get unique sim ID
    student_responses = interview["post_note_inputs"]
    for section in student_responses:
        with st.container(border = True):
            st.subheader(f"{section}", divider = "grey")
            layout1 = st.columns([2, 3])

            with layout1[0]:
                st.html(f"<span style=\"font-size: larger;\"><b>Student Response:</b></span>")
                st.write(student_responses[section])

            with layout1[1]:
                if len(evaluation[section]) > 1:
                    parts = list(evaluation[section].keys())
                    tabs = st.tabs(parts)
                    for i, part in enumerate(parts):
                        with tabs[i]:
                            display_part(evaluation, section, part, sim_id)
                else:
                    display_part(evaluation, section, section, sim_id)
        
    return evaluation


def display_section(evaluations: dict, category: str, part: str) -> None:
    rubric = RUBRIC[category][part] if part else RUBRIC[category]
    df = {'evaler': [], 'score': []}
    for i in range(rubric['features']):
        df[string.ascii_lowercase[i]] = []
    df['comment'] = []

    for evaler in list(evaluations.keys()):
        df['evaler'].append(evaler)
        if evaluations[evaler]:
            inputs = evaluations[evaler]['evaluation'][category][part] if part else evaluations[evaler]['evaluation'][category]
            for key, value in inputs.items():
                if key not in ['comment', 'features', 'score']: continue
                elif key == 'features':
                    for k, v in inputs['features'].items(): 
                        df[k].append(v)
                elif key == 'score':
                    if value is not None:
                        value = int(value)
                    df[key].append(value)
                else:
                    df[key].append(value)
        else:
            for key in df: 
                if key != 'evaler': df[key].append(None)

    config = {
        'evaler': st.column_config.Column("Evaluator", width="small", pinned=True),
        'score': st.column_config.Column(f"Score / {rubric['points']}", width="small"),
        'comment': st.column_config.Column(f"Comment", width="large")
    }
    df = pd.DataFrame(df)
    st.dataframe(df, column_config=config, hide_index=True, use_container_width=True)

    with st.container(border=True):
        st.write("**Rubric:**")
        st.html(rubric["html"])
        with st.expander("Description"):
            st.write(rubric["title"] + ": " + rubric["desc"])

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
                            display_section(evaluations, category, part)
                else:
                    display_section(evaluations, category, part=None)


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
