import time
import datetime as date
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

st.set_page_config(page_title = "AIME",
                   page_icon = "🧑‍⚕️",
                   layout = "wide",
                   initial_sidebar_state="collapsed")

if "stage" not in st.session_state:
    st.session_state["stage"] = LOGIN_PAGE

def set_stage(stage):
    st.session_state["stage"] = stage

if st.session_state["stage"] == LOGIN_PAGE:
    st.write("Welcome, and thank you for volunteering to participate in this beta test! This is an application where you will virtually simulate an interview with a patient, after which you will provide a post note based on it and then automatically receive feedback on your performance.")
    st.write("Please follow the directions on each page to work through the whole application, and take notes on where there is potential room for improvement.")
    st.write("Begin by logging in!")
    
    layout1 = st.columns([2, 3, 2])
    with layout1[1]:
        st.title("Virtual Patient (BETA)")
        st.write("For beta testing use only.")

        username = st.text_input("Username:")
        password = st.text_input("Password:", type = "password")

        layout12b = layout1[1].columns(5)
        if layout12b[2].button("Log in"):
            if username and password == LOGIN_PASS:
                st.session_state["username"] = username
                st.write("Authentication successful!")
                time.sleep(1)
                set_stage(SETTINGS)
                st.rerun()
            else:
                st.write("Password incorect.")


if st.session_state["stage"] == SETTINGS:
    st.session_state["interview"] = None
    st.session_state["messages"] = []
    st.session_state["convo_memory"] = []
    st.session_state["convo_summary"]=""
    st.session_state["convo_file"] = None
    st.session_state["convo_prompt"] = ""
    # st.session_state["sent"] = False
    st.session_state["start_time"] = date.datetime.now()
    st.session_state["tokens"] = {"convo": {"input": 0, "output": 0},
                                  "class": {"input": 0, "output": 0},
                                  "diag": {"input": 0, "output": 0}}

    layout1 = st.columns([1, 3, 1])
    with layout1[1]:
        st.title("Patient Settings")
        patient_name = st.selectbox("Which patient would you like to interview?", 
                                    ["Jeffrey Smith", "Jenny Smith", "Samuel Thompson", "Sarah Thompson"],
                                    index = None,
                                    placeholder = "Select patient...")
        if patient_name: 
            st.session_state["interview"] = Interview.build(username = st.session_state["username"], 
                                                            patient = Patient.build(patient_name))

        if st.session_state["interview"]: 
            # st.session_state["sent"]==False
            st.button("Start Interview", on_click=set_stage, args=[CHAT_SETUP])


if st.session_state["stage"] == CHAT_SETUP:
    st.session_state["convo_prompt"] = st.session_state["interview"].patient.convo_prompt
    # if(st.session_state["sent"]==False):
    #     st.session_state["interview"].start_time = str(st.session_state["start_time"])
        # collection.insert_one(st.session_state["interview"].model_dump())
        # st.session_state["sent"]==True

    set_stage(CHAT_INTERFACE_VOICE)


if st.session_state["stage"] == CHAT_INTERFACE_VOICE:
    layout1 = st.columns([1, 3, 1])
    with layout1[1]:
        st.title("Interview")
        st.write("You may now begin your interview with " + st.session_state["interview"].patient.id + ". Start by introducing yourself.")
        st.write("""Click the Start Recording button to start recording your voice input to the virtual patient.
                The button will then turn into a Stop button, which you can click when you are done talking.
                Click the Restart button to restart the interview, and the End Interview button to go to the download screen.""")

        audio = audiorecorder("Start Recording", "Stop")
        
        container = st.container(height=300)

        for message in st.session_state["interview"].messages:
            with container:
                with st.chat_message(message.role):
                    st.markdown(message.content)

        if len(audio) > 0:
            user_input = transcribe_voice(audio)
            with container:
                with st.chat_message("User"):
                    st.markdown(user_input)
            
            response, speech = get_chat_output(user_input)

            with container:
                with st.chat_message("AI"): # Needs avatar eventually
                    st.markdown(response)
                    play_voice(speech)

        columns = st.columns(4)
        columns[1].button("Restart", on_click=set_stage, args=[SETTINGS])
        columns[2].button("End Interview", on_click=set_stage, args=[PHYSICAL_ECG_SCREEN])


# if st.session_state["stage"] == KEY_PHYSICALS:
#     layout1 = st.columns([2, 3, 2])
#     with layout1[1]:
#         st.title("Key Physical Exam Information")
#         findings = st.text_area(label = "Based on your interview with the patient, state the key physical examination findings that you would look for. You will be provided the actual exam results on the next screen.",
#                                 height = 200)

#         layout11 = st.columns([1, 1, 1])
#         if layout11[1].button("Next", use_container_width=True):
#             st.session_state["interview"].add_key_findings(findings)
#             set_stage(PHYSICAL_ECG_SCREEN)
#             st.rerun()


if st.session_state["stage"] == PHYSICAL_ECG_SCREEN:
    
    layout1 = st.columns([1, 3, 1])
    with layout1[1].container():
        st.title("Physical Examination")
        st.write("Now that you've taken a chance to speak with the patient, you can take a chance to take a look at data obtained during a physical. Review it before proceeding.")
        
        st.divider()
        physical_exam_doc = Document(st.session_state["interview"].patient.physical)
        for paragraph in physical_exam_doc.paragraphs:
            st.write(paragraph.text)
        st.divider()

        layout11 = st.columns([1, 1, 1])
        layout11[1].button("Proceed to Post Note", on_click=set_stage, args = [DIAGNOSIS], use_container_width=True)


if st.session_state["stage"] == DIAGNOSIS:
    st.write("Write your post note as directed and click \"Get Feedback\" to get your feedback/scores.")
    st.write("If you click one of the \"TEST CASE\" buttons, the post note will automatically be filled in and feedback will be processed on those example inputs.")
    st.divider()

    # 2 column full width layout
    layout1 = st.columns([1, 1])

    # User inputs
    summary = layout1[0].text_area(label = "**Summary Statement:** Provide a concise summary statement that uses semantic vocabulary to highlight the most important elements from history and exam to interpret and represent the patient’s main problem.", height = 200)
    assessment = layout1[0].text_area(label = "**Assessment**: Provide a differential diagnosis and explain the reasoning behind each diagnosis.", height = 200)
    plan = layout1[0].text_area(label = "**Plan**: Include a diagnostic plan that explains the rationale for your decision. ", height = 200)

    # Interview transcription
    chat_container = layout1[1].container(height=400)
    for message in st.session_state["interview"].messages:
        with chat_container:
            with st.chat_message(message.role):
                st.markdown(message.content)
    # Physical Examination
    with layout1[1].expander("Physical Examination"):
        physical_exam_doc = Document(st.session_state["interview"].patient.physical)
        for paragraph in physical_exam_doc.paragraphs:
            st.write(paragraph.text)

    # 3 buttons: New Interview, Download Interview, Get Feedback
    st.divider()
    layout2 = st.columns([1, 1, 1, 1, 1])

    # New Interview
    layout2[1].button("New Interview", on_click=set_stage, args=[SETTINGS], use_container_width=True)
    
    # # Download Interview
    # currentDateAndTime = date.datetime.now()
    # st.session_state["interview"].date_time = str(currentDateAndTime)
    # date_time = currentDateAndTime.strftime("%d-%m-%y__%H-%M")

    # bio = io.BytesIO()
    # st.session_state["convo_file"] = create_convo_file(st.session_state["interview"].username, 
    #                                                    st.session_state["interview"].patient.id, 
    #                                                    [message.model_dump() for message in st.session_state["interview"].messages])
    # st.session_state["convo_file"].save(bio)

    # date_time = date.datetime.now().strftime("%d-%m-%y__%H-%M")
    # layout12[1].download_button("Download interview", 
    #                             data = bio.getvalue(), 
    #                             file_name = st.session_state["interview"].username + "_" + date_time + ".docx", 
    #                             mime = "docx")
    
    # Test cases
    layout21 = layout2[2].columns([1, 1])
    if layout21[0].button("TEST: BAD", use_container_width=True):
        with open("./IDEA/test_cases/bad.json", "r", encoding="utf8") as bad_json:
            bad_case = json.load(bad_json)
            # print(bad_case)
            # print("\n\n")
            st.session_state["interview"].add_key_findings(bad_case["Key Findings"])
            st.session_state["interview"].add_other_inputs("",
                                                           "",
                                                           bad_case["Summary"], 
                                                           bad_case["Assessment"], 
                                                           bad_case["Plan"])
            # print(st.session_state["interview"].post_note_inputs)
            # print("\n\n")
        set_stage(FEEDBACK_SETUP)
        st.rerun()
    if layout21[1].button("TEST: GOOD", use_container_width=True):
        with open("./IDEA/test_cases/good.json", "r", encoding="utf8") as good_json:
            good_case = json.load(good_json)
            st.session_state["interview"].add_key_findings(good_case["Key Findings"])
            st.session_state["interview"].add_other_inputs("",
                                                           "",
                                                           good_case["Summary"], 
                                                           good_case["Assessment"], 
                                                           good_case["Plan"])
        set_stage(FEEDBACK_SETUP)
        st.rerun()
    
    # Get Feedback
    if layout2[3].button("Get Feedback", use_container_width=True): 
        st.session_state["interview"].add_other_inputs("", "", summary, assessment, plan)
        set_stage(FEEDBACK_SETUP)
        st.rerun()


if st.session_state["stage"] == FEEDBACK_SETUP:
     # Update the database from before

    # collection.replace_one({"username":st.session_state["interview"].username, "start_time":st.session_state["interview"].start_time}, st.session_state["interview"].model_dump())

    st.title("Processing feedback...")
    st.write("This might take a few minutes.")
    st.session_state["interview"].add_feedback()
    # st.json(st.session_state["interview"].model_dump_json())
    st.session_state["interview_dict"] = st.session_state["interview"].model_dump()
    
    set_stage(FEEDBACK_SCREEN)
    st.rerun()


if st.session_state["stage"] == FEEDBACK_SCREEN:
    st.title("Feedback")
    layout1 = st.columns([7, 1])
    layout1[0].write("The \"Interview\" tab shows your interview transcript. The \"Post Note\" tab shows personalized feedback for each of your write-ups based on a detailed IDEA-based rubric. The \"Case Explanation\" tab allows you to download a document with additional details and explanations on the patient case.")
    layout1[1].button("New Interview", on_click=set_stage, args=[SETTINGS])
    layout1[1].button("Back to Login", on_click=set_stage, args=[LOGIN_PAGE])
    
    # Let the display methods cook
    display_Interview(st.session_state["interview"].model_dump())