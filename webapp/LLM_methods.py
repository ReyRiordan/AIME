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
import tempfile
from lookups import *
from website_classes import *
from annotated_text import annotated_text
import json


def transcribe_voice(voice_input):
    client = OpenAI()
    temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    voice_input.export(temp_audio_file.name, format="wav")
    with open(temp_audio_file.name, "rb") as file:
        transcription = client.audio.transcriptions.create(model="whisper-1", 
                                                    file=file, 
                                                    response_format="text")
    
    return transcription


def classifier(category: DataCategory, messages: list[Message]) -> None:
    # Create GPT instance
    llm = ChatOpenAI(api_key=OPENAI_API_KEY, model=CLASS_MODEL, temperature=0.0)
    conversation = ConversationChain(llm=llm, memory=ConversationBufferMemory())
    
    # Get the base class prompt for the category
    prompt_input = category.class_prompt

    # Append applicable messages to prompt
    applicable_messages = []
    for message in messages:
        if message.type == category.type:
            applicable_messages.append(message)
            message_content = message.content.rstrip() + "||"
            prompt_input += message_content

    # Classify
    raw_classification = conversation.predict(input=prompt_input)
    classifications = raw_classification.split("||")[:-1] # Remove empty classification at the end
    all_classifications = [] # list[list[str]]
    for classification in classifications:
        class_list = classification.split() # Split into individual labels by spaces
        for i in range(len(class_list)):
            class_list[i] = class_list[i].replace("_", " ") # Remove underscores from labels
        class_list = [label for label in class_list if label != "Other"] # Remove "Other" labels
        all_classifications.append(class_list) # Appends list of labels (one for each message)
    
    # Assign labels to each message accordingly
    if len(applicable_messages) != len(all_classifications):
        raise ValueError("Number of classifications must match number of applicable messages.")
    for i in range(len(applicable_messages)):
        if all_classifications[i]: # If not an empty list with no labels
            applicable_messages[i].labels[category.name] = all_classifications[i]


def summarizer(LLM: OpenAI, convo_memory: list[dict[str, str]]) -> str:
    messages = [{"role": "system", "content": SUM_PROMPT}]
    dialogue = ""
    for message in convo_memory[1:]:
        if message["role"] == "system":
            dialogue += message["content"] + " \n"
        elif message["role"] == "user":
            dialogue += "User: " + message["content"] + " \n"
        elif message["role"] == "assistant":
            dialogue += "AI: " + message["content"] + "\n"
    messages.append({"role": "user", "content": dialogue})
    raw_summary = LLM.chat.completions.create(model = SUM_MODEL, 
                                              temperature = SUM_TEMP, 
                                              messages = messages)
    summary = raw_summary.choices[0].message.content
    return summary


def get_chat_output(LLM: OpenAI, convo_memory: list[dict[str, str]], user_input: str) -> list[list[dict[str, str]], str]:
    convo_memory.append({"role": "user", "content": user_input})
    response = LLM.chat.completions.create(model = CONVO_MODEL, 
                                           temperature = CHAT_TEMP, 
                                           messages = convo_memory)
    output = response.choices[0].message.content
    convo_memory.append({"role": "assistant", "content": output})
    if len(convo_memory) >= 10:
        summary = summarizer(LLM, convo_memory)
        convo_memory = [convo_memory[0], {"role": "system", "content": ("Summary of conversation so far: \n" + summary)}]
    return convo_memory, output