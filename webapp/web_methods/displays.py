from langchain_community.chat_models import ChatOpenAI
from langchain.chains.conversation.base import ConversationChain
from langchain.memory.buffer import ConversationBufferMemory
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

from lookups import *


def get_webtext(content: str) -> str:
    path = WEBSITE_TEXT[content]
    with open(path, 'r', encoding='utf8') as webtext:
            text = webtext.read()
    return text


def display_DataCategory(category: dict[str, str], checklist: dict[str, bool], weights: dict[str, int], score: int, maxscore: int) -> None:
    with st.container(border = True):
        st.subheader(f":{category['color']}[{category['header']}]: {score}/{maxscore}", divider = category['color'])
        display_labels = [(key, str(weights[key]), "#baffc9" if value else "#ffb3ba") for key, value in checklist.items()]
        annotated_text(display_labels)
        with st.expander("Label Descriptions:"):
            for key, value in checklist.items():
                annotated_text([(key, "", "#baffc9" if value else "#ffb3ba"), " " + LABEL_DESCS[key]])


def display_DataAcquisition(data: dict, messages: list[dict]) -> None:
    layout1 = st.columns([4, 5])
    with layout1[0]:
        for category in data["datacategories"]:
            cat_name = category["name"]
            display_DataCategory(category, 
                                 data["checklists"][cat_name], 
                                 data["weights"][cat_name], 
                                 data["scores"][cat_name], 
                                 data["maxscores"][cat_name])
    
    with layout1[1]:
        st.subheader("Annotated Interview Transcript", divider = "grey")
        chat_container = st.container(height=700)
        for message in messages:
                with chat_container:
                    with st.chat_message(message["role"]):
                        if message["annotation"] is None:
                            st.markdown(message["content"])
                        else:
                            annotated_text((message["content"], message["annotation"], message["highlight"]))


def display_Diagnosis(diagnosis: dict, inputs: dict) -> None:
    scores = diagnosis["scores"]
    maxscores = diagnosis["maxscores"]
    classified = diagnosis["classified"]
    checklists = diagnosis["checklists"]
    weights = diagnosis["weights"]

    with st.container(border = True):
        st.subheader(f"Interpretative Summary: {scores['Summary']}/{maxscores['Summary']}", divider = "grey")
        layout1 = st.columns([1, 1])
        with layout1[0]:
            st.write(inputs["Summary"])
        with layout1[1]:
            display_labels = [(key, str(weights["Summary"][key]), "#baffc9" if value else "#ffb3ba") for key, value in checklists["Summary"].items()]
            annotated_text(display_labels)
            with st.expander("Label Descriptions:"):
                for key, value in checklists["Summary"].items():
                    annotated_text([(key, "", "#baffc9" if value else "#ffb3ba"), " " + LABEL_DESCS[key]])

    with st.container(border = True):
        st.subheader(f"Potential Diagnoses: {scores['Potential']}/{maxscores['Potential']}", divider = "grey")
        layout2 = st.columns([1, 1])
        with layout2[0]:
            user_potential = [(key, value, "#baffc9" if value in checklists["Potential"] else "#ffb3ba") for key, value in classified["Potential"].items()]
            annotated_text(["Your answers: "] + user_potential)
        with layout2[1]:
            valid_potential = [(key, str(weights["Potential"][key]), "#baffc9" if value else "#ffb3ba") for key, value, in checklists["Potential"].items()]
            annotated_text(["Valid answers: "] + valid_potential)
        
    with st.container(border = True):
        st.subheader(f"Rationale: {scores['Rationale']}/{maxscores['Rationale']}", divider = "grey")
        layout3 = st.columns([1, 1])
        with layout3[0]:
            st.write(inputs["Rationale"])
        with layout3[1]:
            for key, value in checklists["Rationale"].items():
                annotated_text((key, str(weights["Rationale"][key]), "#baffc9" if value else "#ffb3ba"))

    with st.container(border = True):
        st.subheader(f"Final Diagnosis: {scores['Final']}/{maxscores['Final']}", divider = "grey")
        layout4 = st.columns([1, 1])
        with layout4[0]:
            user_final = [(key, value, "#baffc9" if value in checklists["Final"] else "#ffb3ba") for key, value in classified["Final"].items()]
            annotated_text("Your answer: ", user_final)
        with layout4[1]:
            valid_final = [(key, str(weights["Final"][key]), "#baffc9" if value else "#ffb3ba") for key, value, in checklists["Final"].items()]
            annotated_text("Valid answer(s): ", valid_final)


def display_Interview(interview: dict) -> None:
    st.write(f"{interview['username']} @ {interview['date_time']}, Patient: {interview['patient']['name']}")

    if interview["feedback"]:
        data, diagnosis, explanation = st.tabs(["Data Acquisition", "Diagnosis", "Case Explanation"])
        with data:
            display_DataAcquisition(interview["feedback"]["Data Acquisition"], interview["messages"])
        with diagnosis:
            display_Diagnosis(interview["feedback"]["Diagnosis"], interview["diagnosis_inputs"])
        with explanation:
            explanation_file = st.session_state["interview"].get_patient().explanation
            with open(explanation_file, "rb") as pdf_file:
                explanation = pdf_file.read()
                st.download_button("Download Case Explanation (PDF)", explanation, explanation_file)
    else:
        chat_container = st.container(height=300)
        for message in st.session_state["interview"]["messages"]:
            with chat_container:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        if interview["diagnosis_inputs"]:
            diagnosis_inputs = interview["diagnosis_inputs"]
            st.divider()
            st.write("Interpretative Summary: " + diagnosis_inputs["Summary"])
            st.write("Potential Diagnoses: " + ", ".join(diagnosis_inputs["Potential"]))
            st.write("Rationale: " + diagnosis_inputs["Rationale"])
            st.write("Final Diagnosis: " + diagnosis_inputs["Final"])

#TODO: NOT EVEN CLOSE TO DONE, PROBLEM FOR @ALI

# def display_Interview_NEW(interview:Interview)->None:
#     st.write(f"{interview.username} @ {interview.date_time}, Patient {interview.patient.name}")

#     if interview.feedback:
#         data, diagnosis, empathy = st.tabs(["Data Acquisition", "Diagnosis", "Empathy"])
#         with data:
#             display_DataAcquisition_NEW(interview.feedback.data_acquisition, interview.messages)
#         with diagnosis:
#             display_Diagnosis_NEW(interview.feedback.diagnosis, interview.user_diagnosis)
#     else:
#         chat_container = st.container(height=300)
#         for message in interview.messages:
#             with chat_container:
#                 with st.chat_message(message.role):
#                     st.markdown(message.content)
                    
#         if interview.user_diagnosis:
#             user_diagnosis = interview.user_diagnosis
#             st.divider()
#             st.write("Interpretative Summary: " + user_diagnosis["Summary"])
#             st.write("Main Diagnosis: " + user_diagnosis["Main"])
#             st.write("Main Rationale: " + user_diagnosis["Rationale"])
#             st.write("Secondary Diagnoses: " + ", ".join(user_diagnosis["Secondary"]))

# def display_DataAcquisition_NEW(data:DataAcquisition, messages:List[Message])->None:
#     layout1 = st.columns([4, 5])
#     with layout1[0]:
#         for category in data.datacategories:
#             cat_name = category.name
#             display_DataCategory(category, 
#                                  data.checklists[cat_name], 
#                                  data["weights"][cat_name], 
#                                  data["scores"][cat_name], 
#                                  data["maxscores"][cat_name])
    
#     chat_container = layout1[1].container(height=500)
#     for message in messages:
#             with chat_container:
#                 with st.chat_message(message["role"]):
#                     if message["annotation"] is None:
#                         st.markdown(message["content"])
#                     else:
#                         annotated_text((message["content"], message["annotation"], message["highlight"]))