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
import tempfile
from constants import *
from langchain_community.chat_models import ChatOpenAI
from langchain.chains.conversation.base import ConversationChain
from langchain.memory.buffer import ConversationBufferMemory
from virtual_patient.patients import GPT_Patient
from website_classes import Message


def create_interview_file(username: str, patient: str, messages: list[dict[str, str]], grading_results: dict[str,bool]) -> Document:
    interview = Document()
    heading = interview.add_paragraph("User: " + username + ", ")
    currentDateAndTime = date.datetime.now()
    date_time = currentDateAndTime.strftime("%d-%m-%y__%H-%M")
    heading.add_run("Date: " + date_time + ", ")
    heading.add_run("Patient: " + patient)
    for message in messages:
        interview.add_paragraph(message["role"] + ": " + message["content"])
    interview.add_paragraph("Grading Criteria")
    for message in grading_results:
        msg=interview.add_paragraph(message[0])
        msg.add_run(message[1]).bold=True
    return interview


def send_email(bio, EMAIL_TO_SEND, username, date_time, feedback):
    message = Mail(
        from_email = 'rutgers.aime@gmail.com',
        to_emails = EMAIL_TO_SEND,
        subject = "Conversation from " + username + " at time " + date_time,
        html_content = feedback)
    attachment = Attachment()
    encoded = base64.b64encode(bio.getvalue()).decode()
    attachment.file_content=FileContent(encoded)
    attachment.file_type = FileType('docx')
    attachment.file_name = FileName(username + "_" + date_time + ".docx")
    attachment.disposition = Disposition('attachment')
    attachment.content_id = ContentId('docx')
    message.attachment = attachment
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except: 
        print("ERROR ENCOUNTERED SENDING MESSAGE\n")


def transcribe_voice(voice_input, OPENAI_API_KEY):
    client = OpenAI()
    temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    voice_input.export(temp_audio_file.name, format="wav")
    with open(temp_audio_file.name, "rb") as file:
        transcription = client.audio.transcriptions.create(model="whisper-1", 
                                                    file=file, 
                                                    response_format="text")
    
    return transcription


def classifier(prompt_input: str, type: str, messages: list[Message], OPENAI_API_KEY: str) -> list[list[str]]:
    # Create GPT instance
    llm = ChatOpenAI(api_key=OPENAI_API_KEY, model=MODEL, temperature=0.0)
    conversation = ConversationChain(llm=llm, memory=ConversationBufferMemory())
    
    # Append applicable messages to prompt
    for message in messages:
        if message.type == type:
            message_content = message.content.rstrip() + "||"
            prompt_input += message_content

    # Classify
    raw_classification = conversation.predict(input=prompt_input)
    classifications = raw_classification.split("||")
    output = [] 
    for classification in classifications:
        class_list = classification.split()
        for i in range(len(class_list)):
            class_list[i] = class_list[i].replace("_", " ")
        class_list = [label for label in class_list if label != "Other"]
        output.append(class_list)
        
    return output


def annotate(patient: GPT_Patient, messages: list[Message], OPENAI_API_KEY: str) -> None:
    # Get all classification labels
    with open(CLASSIFY_GEN_PROMPT, "r", encoding="utf8") as classify_gen:
        class_gen_prompt = classify_gen.read()
    with open(CLASSIFY_DIMS_PROMPT, "r", encoding="utf8") as classify_dims:
        class_dims_prompt = classify_dims.read()
    input_labeled_gen = classifier(class_gen_prompt, "input", messages, OPENAI_API_KEY)
    input_labeled_asoc = classifier(patient.class_asoc_prompt, "input", messages, OPENAI_API_KEY)
    input_labeled_risk = classifier(patient.class_risk_prompt, "input", messages, OPENAI_API_KEY)
    output_labeled_dims = classifier(class_dims_prompt, "output", messages, OPENAI_API_KEY)
    
    # Assign all labels accordingly
    input_index = 0
    output_index = 0
    for message in messages:
        if message.type == "input":
            if input_labeled_gen[input_index]: message.labels_gen = input_labeled_gen[input_index]
            if input_labeled_asoc[input_index]: message.labels_asoc = input_labeled_asoc[input_index]
            if input_labeled_risk[input_index]: message.labels_risk = input_labeled_risk[input_index]
            input_index += 1
        elif message.type == "output":
            if output_labeled_dims[output_index]: message.labels_dims = output_labeled_dims[output_index]
            output_index += 1
    
    # Add color and annotation after all labels are assigned
    for message in messages:
        message.add_color()
        message.add_annotation()


def grade_data_acquisition(patient: GPT_Patient, messages: list[Message]) -> [dict[dict[str, bool]], dict[str, list[int]]]:
    # Helper dict with attribute names
    categories = {"gen": {"message": "labels_gen", "patient": "weights_gen"}, 
                  "dims": {"message": "labels_dims", "patient": "weights_dims"}, 
                  "asoc": {"message": "labels_asoc", "patient": "weights_asoc"}, 
                  "risk": {"message": "labels_risk", "patient": "weights_risk"}}
    
    # Initialize label grades
    all_grades = {category: {label: False for label in getattr(patient, categories[category]["patient"])} for category in categories}

    # Initialize scores
    all_scores = {category: [0, 0] for category in categories}

    # Iterate through messages and update label grades
    for message in messages:
        for category in categories:
            labels = getattr(message, categories[category]["message"])
            if labels:
                for label in labels:
                    all_grades[category][label] = True

    # Get scores and max scores
    for category in categories:
        weights = getattr(patient, categories[category]["patient"])
        for label in weights:
            if all_grades[category][label]: all_scores[category][0] += weights[label]
            all_scores[category][1] += weights[label]

    return [all_grades, all_scores]