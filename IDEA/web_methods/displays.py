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


def display_PostNote(feedback: dict, inputs: dict, short: bool) -> None:
    # print(feedback)
    inst = st.toggle("INSTRUCTOR VIEW")
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
                                st.write(dd["rubric"])
                            if inst:
                                with st.expander("Thought process"):
                                    if dd["thought"]: st.write(dd["thought"])
                            st.divider()
                else:
                    if inst: st.write(f"**Score: {d['score']}/{d['max']}**")
                    st.write(d["comment"])
                    with st.expander("Rubric"):
                        st.write(d["desc"])
                        st.write(d["rubric"])
                    if inst:
                        with st.expander("Thought process"):
                            if d["thought"]: st.write(d["thought"])
    


def display_DataAcquisition(data_acquisition: dict, messages: list[dict], label_descs: dict) -> None:
    layout1 = st.columns([4, 5])

    with layout1[0]:
        for category in data_acquisition["data_categories"]:
            grades = data_acquisition["grades"][category["name"]]
            scores = data_acquisition["scores"][category["name"]]
            with st.container(border = True):
                st.subheader(f":{category['color']}[{category['header']}]: {scores['raw']}/{scores['max']}", divider = category['color'])
                display_labels = [(label, str(value["weight"]), "#baffc9" if value["score"] else "#ffb3ba") for label, value in grades.items()]
                annotated_text(display_labels)
                with st.expander("Label Descriptions:"):
                    for label, value in grades.items():
                        annotated_text([(label, "", "#baffc9" if value["score"] else "#ffb3ba"), " " + label_descs[label]])
    
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


def display_Diagnosis(diagnosis: dict, inputs: dict, label_descs: dict) -> None:
    grades = diagnosis["grades"]
    matches = diagnosis["matches"]
    scores = diagnosis["scores"]
    GREEN = "#baffc9"
    RED = "#ffb3ba"

    # Summary
    with st.container(border = True):
        st.subheader(f"Interpretative Summary: {scores['Summary']['raw']}/{scores['Summary']['max']}", divider = "grey")
        layout1 = st.columns([1, 1])
        with layout1[0]:
            st.write("**Your answer:**")
            st.write(inputs["Summary"])
        with layout1[1]:
            st.write("**Scoring:**")
            display_labels = [(label, str(value["weight"]), GREEN if value["score"] else RED) for label, value in grades["Summary"].items()]
            annotated_text(display_labels)
            with st.expander("**Label Descriptions:**"):
                for label, value in grades["Summary"].items():
                    annotated_text([(label, "", GREEN if value["score"] else RED), " " + label_descs[label]])

    # Potential diagnoses
    with st.container(border = True):
        st.subheader(f"Potential Diagnoses: {scores['Potential']['raw']}/{scores['Potential']['max']}", divider = "grey")
        layout2 = st.columns([1, 1])
        with layout2[0]:
            st.write("**Your answer(s):**")
            user_potential = [(input, match, GREEN if match in grades["Potential"] else RED) for input, match in matches["Potential"].items()]
            annotated_text(user_potential)
        with layout2[1]:
            st.write("**Valid answers:**")
            valid_potential = [(condition, str(value["weight"]), GREEN if value["score"] else RED) for condition, value, in grades["Potential"].items()]
            annotated_text(valid_potential)
    
    # Rationale
    with st.container(border = True):
        st.subheader(f"Rationale: {scores['Rationale']['total']['raw']}/{scores['Rationale']['total']['max']}", divider = "grey",
                     help = ":large_green_square: means the reasoning SUPPORTS the diagnosis, while :large_red_square: means the opposite.")
        layout3 = st.columns([1, 1])
        with layout3[0]:
            st.write("**Your answer:**")
            st.write(inputs["Rationale"])
        with layout3[1]:
            st.write("**Scoring:**")
            if grades["Rationale"]["yes"]:
                for condition in grades["Rationale"]["yes"]:
                    with st.expander(f"**{condition}: {scores['Rationale'][condition]['raw']}/{scores['Rationale'][condition]['max']}**"):
                        for reasoning in grades["Rationale"]["yes"][condition]:
                            sign = ":large_green_square:" if reasoning["sign"] else ":large_red_square:"
                            annotated_text((f"{sign} {reasoning['desc']}", str(reasoning["weight"]), GREEN if reasoning["score"] else RED))
            else:
                st.write("We currently have no way to grade your rationale if you did not list any correct potential diagnoses.")
            with st.expander("**Reasoning for potential diagnoses you didn't list:**"):
                for condition in grades["Rationale"]["no"]:
                    st.write(f"**{condition}: -/{scores['Rationale'][condition]['max']}**")
                    for reasoning in grades["Rationale"]["no"][condition]:
                        sign = ":large_green_square:" if reasoning["sign"] else ":large_red_square:"
                        annotated_text((f"{sign} {reasoning['desc']}", str(reasoning["weight"]), "#ededed"))

    # Final Diagnosis
    with st.container(border = True):
        st.subheader(f"Final Diagnosis: {scores['Final']['raw']}/{scores['Final']['max']}", divider = "grey")
        layout4 = st.columns([1, 1])
        with layout4[0]:
            st.write("**Your answer:**")
            user_final = [(input, match, GREEN if match in grades["Final"] else RED) for input, match in matches["Final"].items()]
            annotated_text("Your answer: ", user_final)
        with layout4[1]:
            st.write("**Valid answer(s):**")
            valid_final = [(condition, str(value["weight"]), GREEN if value["score"] else RED) for condition, value, in grades["Final"].items()]
            annotated_text(valid_final)


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

#TODO: NOT EVEN CLOSE TO DONE, PROBLEM FOR @ALI

# def display_Interview_NEW(interview:Interview)->None:
#     st.write(f"{interview.username} @ {interview.start_time}, Patient {interview.patient.name}")

#     if interview.feedback:
#         data, diagnosis, empathy = st.tabs(["Data Acquisition", "Diagnosis", "Empathy"])
#         with data:
#             display_DataAcquisition_NEW(interview.feedback.data_acquisition, interview.messages)
#         with diagnosis:
#             display_Diagnosis_NEW(interview.feedback.diagnosis, interview.diagnosis_inputs)
#     else:
#         chat_container = st.container(height=300)
#         for message in interview.messages:
#             with chat_container:
#                 with st.chat_message(message.role):
#                     st.markdown(message.content)
                    
#         if interview.diagnosis_inputs:
#             diagnosis_inputs = interview.diagnosis_inputs
#             st.divider()
#             st.write("Interpretative Summary: " + diagnosis_inputs["Summary"])
#             st.write("Main Diagnosis: " + diagnosis_inputs["Potential"])
#             st.write("Main Rationale: " + diagnosis_inputs["Rationale"])
#             st.write("Secondary Diagnoses: " + ", ".join(diagnosis_inputs["Final"]))

# def display_DataAcquisition_NEW(data:DataAcquisition, messages:List[Message])->None:
#     layout1 = st.columns([4, 5])
#     with layout1[0]:
#         for category in data.datacategories:
#             cat_name = category.name
#             display_DataCategory_NEW(category, 
#                                  data.checklists[cat_name], 
#                                  data.weights[cat_name], 
#                                  data.scores[cat_name], 
#                                  data.maxscores[cat_name])
    
#     chat_container = layout1[1].container(height=500)
#     for message in messages:
#             with chat_container:
#                 with st.chat_message(message.role):
#                     if message.annotation is None:
#                         st.markdown(message.content)
#                     else:
#                         annotated_text((message.content, message.annotation, message.highlight))


# def display_Diagnosis_NEW(diagnosis: Diagnosis, inputs: dict) -> None:
#     scores = diagnosis.scores
#     maxscores = diagnosis.maxscores
#     classified = diagnosis.classified
#     checklists = diagnosis.checklists
#     weights = diagnosis.weights

#     with st.container(border = True):
#         st.subheader(f"Interpretative Summary: {scores['Summary']}/{maxscores['Summary']}", divider = "grey")
#         layout1 = st.columns([1, 1])
#         with layout1[0]:
#             st.write("**Your answer:**")
#             st.write(inputs["Summary"])
#         with layout1[1]:
#             st.write("**Scoring:**")
#             display_labels = [(key, str(weights["Summary"][key]), "#baffc9" if value else "#ffb3ba") for key, value in checklists["Summary"].items()]
#             annotated_text(display_labels)
#             with st.expander("**Label Descriptions:**"):
#                 for key, value in checklists["Summary"].items():
#                     annotated_text([(key, "", "#baffc9" if value else "#ffb3ba"), " " + LABEL_DESCS[key]])

#     with st.container(border = True):
#         st.subheader(f"Potential Diagnoses: {scores['Potential']}/{maxscores['Potential']}", divider = "grey")
#         layout2 = st.columns([1, 1])
#         with layout2[0]:
#             st.write("**Your answer(s):**")
#             user_potential = [(key, value, "#baffc9" if value in checklists["Potential"] else "#ffb3ba") for key, value in classified["Potential"].items()]
#             annotated_text(user_potential)
#         with layout2[1]:
#             st.write("**Valid answers:**")
#             valid_potential = [(key, str(weights["Potential"][key]), "#baffc9" if value else "#ffb3ba") for key, value, in checklists["Potential"].items()]
#             annotated_text(valid_potential)
        
#     with st.container(border = True):
#         st.subheader(f"Rationale: {scores['Rationale']}/{maxscores['Rationale']}", divider = "grey")
#         layout3 = st.columns([1, 1])
#         with layout3[0]:
#             st.write("**Your answer:**")
#             st.write(inputs["Rationale"])
#         with layout3[1]:
#             st.write("**Scoring:**")
#             for condition in weights["Rationale"]:
#                 if condition in checklists["Rationale"]:
#                     with st.expander(f"**{condition}:**"):
#                         for statement, checked in checklists["Rationale"][condition].items():
#                             annotated_text((statement, str(weights["Rationale"][condition][statement]), "#baffc9" if checked else "#ffb3ba"))
#             with st.expander("**Reasoning for potential diagnoses you didn't list:**"):
#                 for condition in weights["Rationale"]:
#                     if condition not in checklists["Rationale"]:
#                         for statement, weight in weights["Rationale"][condition].items():
#                             annotated_text((statement, str(weight), "#ededed"))

#     with st.container(border = True):
#         st.subheader(f"Final Diagnosis: {scores['Final']}/{maxscores['Final']}", divider = "grey")
#         layout4 = st.columns([1, 1])
#         with layout4[0]:
#             st.write("**Your answer:**")
#             user_final = [(key, value, "#baffc9" if value in checklists["Final"] else "#ffb3ba") for key, value in classified["Final"].items()]
#             annotated_text("Your answer: ", user_final)
#         with layout4[1]:
#             st.write("**Valid answer(s):**")
#             valid_final = [(key, str(weights["Final"][key]), "#baffc9" if value else "#ffb3ba") for key, value, in checklists["Final"].items()]
#             annotated_text(valid_final)


# def display_DataCategory_NEW(category: DataCategory, checklist: dict[str, bool], weights: dict[str, int], score: int, maxscore: int) -> None:
#     with st.container(border = True):
#         st.subheader(f":{category.color}[{category.header}]: {score}/{maxscore}", divider = category['color'])
#         display_labels = [(key, str(weights[key]), "#baffc9" if value else "#ffb3ba") for key, value in checklist.items()]
#         annotated_text(display_labels)
#         with st.expander("Label Descriptions:"):
#             for key, value in checklist.items():
#                 annotated_text([(key, "", "#baffc9" if value else "#ffb3ba"), " " + LABEL_DESCS[key]])
