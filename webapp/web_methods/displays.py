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

from lookups import *
from web_classes import *


def get_webtext(content: str) -> str:
    path = WEBSITE_TEXT[content]
    with open(path, 'r', encoding='utf8') as webtext:
            text = webtext.read()
    return text


def display_DataCategory(category: dict[str, str], checklist: dict[str, bool], weights: dict[str, int], score: int, maxscore: int) -> None:
    st.header(f":{category["color"]}[{category["header"]}]: {score}/{maxscore}", divider = category["color"])
    display_labels = [(key, str(weights[key]), "#baffc9" if value else "#ffb3ba") for key, value in checklist.items()]
    annotated_text(display_labels)


def display_DataAcquisition(data: dict, messages: list[dict]) -> None:
    chat_container = st.container(height=300)
    for message in messages:
            with chat_container:
                with st.chat_message(message["role"]):
                    if message["annotation"] is None:
                        st.markdown(message["content"])
                    else:
                        annotated_text((message["content"], message["annotation"], message["highlight"]))

    for category in data["datacategories"]:
        cat_name = category["name"]
        display_DataCategory(category, data["checklists"][cat_name], data["weights"][cat_name], data["scores"][cat_name], data["maxscores"][cat_name])


def display_Diagnosis(diagnosis: dict, userdiagnosis: dict) -> None:
    score = diagnosis["score"]
    maxscore = diagnosis["score"]
    st.header(f"Diagnosis: {score}/{maxscore}")
    st.divider()
    st.write("Main Diagnosis: " + userdiagnosis["main_diagnosis"])
    st.write("Main Rationale: " + userdiagnosis["main_rationale"])
    st.write("Secondary Diagnoses: " + ", ".join(userdiagnosis["secondary_diagnoses"]))


def display_Interview(interview: dict) -> None:
    st.write(interview["username"] + " @ " + interview["date_time"])

    if interview["feedback"]:
        data, diagnosis, empathy = st.tabs(["Data Acquisition", "Diagnosis", "Empathy"])
        with data:
            display_DataAcquisition(interview["feedback"]["Data Acquisition"], interview["messages"])
        with diagnosis:
            display_Diagnosis(interview["feedback"]["Diagnosis"], interview["userdiagnosis"])
    else:
        chat_container = st.container(height=300)
        for message in st.session_state["interview"]["messages"]:
            with chat_container:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
        if interview["userdiagnosis"]:
            userdiagnosis = interview["userdiagnosis"]
            st.divider()
            st.write("Main Diagnosis: " + userdiagnosis["main_diagnosis"])
            st.write("Main Rationale: " + userdiagnosis["main_rationale"])
            st.write("Secondary Diagnoses: " + ", ".join(userdiagnosis["secondary_diagnoses"]))