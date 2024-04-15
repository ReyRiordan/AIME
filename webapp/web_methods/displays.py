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
    st.subheader(f":{category['color']}[{category['header']}]: {score}/{maxscore}", divider = category['color'])
    display_labels = [(key, str(weights[key]), "#baffc9" if value else "#ffb3ba") for key, value in checklist.items()]
    annotated_text(display_labels)


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
    
    chat_container = layout1[1].container(height=500)
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

    layout1 = st.columns([1, 1])

    with layout1[0].container(border = True):
        st.subheader(f"Interpretative Summary: {scores['Summary']}/{maxscores['Summary']}", divider = "grey")
        st.write(inputs["Summary"])
        display_labels = [(key, str(weights["Summary"][key]), "#baffc9" if value else "#ffb3ba") for key, value in checklists["Summary"].items()]
        annotated_text(display_labels)

    with layout1[0].container(border = True):
        st.subheader(f"Main Diagnosis: {scores['Main']}/{maxscores['Main']}", divider = "grey")
        user_main = [(key, value, "#baffc9" if value in checklists["Main"] else "#ffb3ba") for key, value in classified["Main"].items()]
        annotated_text("Your answer(s): ", user_main)
        valid_main = [(key, str(weights["Main"][key]), "#baffc9" if value else "#ffb3ba") for key, value, in checklists["Main"].items()]
        annotated_text("Valid answer(s): ", valid_main)

    with layout1[0].container(border = True):
        st.subheader("Main Rationale: ")
        st.write("Your answer: " + inputs["Main"])
        st.write("Example answer: " + "COMING SOON")

    with layout1[0].container(border = True):
        st.subheader(f"Secondary Diagnoses: {scores['Secondary']}/{maxscores['Secondary']}", divider = "grey")
        user_secondary = [(key, value, "#baffc9" if value in checklists["Secondary"] else "#ffb3ba") for key, value in classified["Secondary"].items()]
        annotated_text(["Your answer(s): "] + user_secondary)
        valid_secondary = [(key, str(weights["Secondary"][key]), "#baffc9" if value else "#ffb3ba") for key, value, in checklists["Secondary"].items()]
        annotated_text(["Valid answer(s): "] + valid_secondary)

    with layout1[1].container():
        st.write("Insert explanations, examples, or additional feedback here...")


def display_Interview(interview: dict) -> None:
    st.write(f"{interview['username']} @ {interview['date_time']}, Patient: {interview['patient']['name']}")

    if interview["feedback"]:
        data, diagnosis, empathy = st.tabs(["Data Acquisition", "Diagnosis", "Empathy"])
        with data:
            display_DataAcquisition(interview["feedback"]["Data Acquisition"], interview["messages"])
        with diagnosis:
            display_Diagnosis(interview["feedback"]["Diagnosis"], interview["user_diagnosis"])
    else:
        chat_container = st.container(height=300)
        for message in st.session_state["interview"]["messages"]:
            with chat_container:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        if interview["user_diagnosis"]:
            user_diagnosis = interview["user_diagnosis"]
            st.divider()
            st.write("Interpretative Summary: " + user_diagnosis["Summary"])
            st.write("Main Diagnosis: " + user_diagnosis["Main"])
            st.write("Main Rationale: " + user_diagnosis["Rationale"])
            st.write("Secondary Diagnoses: " + ", ".join(user_diagnosis["Secondary"]))

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