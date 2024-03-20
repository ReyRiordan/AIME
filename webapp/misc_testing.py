from langchain_community.chat_models import ChatOpenAI
from langchain.chains.conversation.base import ConversationChain
from langchain.memory.buffer import ConversationBufferMemory
import time
import datetime as date
from docx import Document
import io
import os
import streamlit as st
import streamlit.components.v1 as components
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName,
    FileType, Disposition, ContentId)
from audiorecorder import audiorecorder
from openai import OpenAI
import tempfile
from annotated_text import annotated_text
import json

from lookups import *
from web_classes import *
from web_methods import *


# # role = {"Personal Details": [{"detail": "Sex", "line": "Female"}, 
# #                              {"detail": "Name", "line": "Jackie Smith"}, 
# #                              {"detail": "Birthdate", "line": "December 5th 1979"}, 
# #                              {"detail": "Personality", "line": "Bright and approachable"}, 
# #                              {"detail": "Tone", "line": "Worried and nervous"}, 
# #                              {"detail": "Manner of Speech", "line": "Respectful"}], 
# #         "Chief Concern": "You came to the hospital because you are experiencing pain in your chest. You are nervous about your symptoms because your father died suddenly of a heart attack when he was 50.", 
# #         "History of Present Illness": [{"lock": False, "dim": "Onset", "line": "pain it was very mild at first and has gotten much worse over the day today. You weren’t really doing anything in particular when you first noticed the pain."}, 
# #                                        {"lock": False, "dim": "Quality", "line": "sharp, stabbing pain in chest"}, 
# #                                        {"lock": False, "dim": "Location", "line": "center of chest"}, 
# #                                        {"lock": False, "dim": "Timing", "line": "experiencing chest pain for about a day and half"}, 
# #                                        {"lock": False, "dim": "Pattern", "line": "constant"}, 
# #                                        {"lock": False, "dim": "Severity", "line": "the pain is very severe"}, 
# #                                        {"lock": True, "dim": "Prior History", "line": "you've never had chest pain like you are experiencing now"}, 
# #                                        {"lock": True, "dim": "Radiation", "line": "you also notice a pain in along the upper part of your back along both shoulders"}, 
# #                                        {"lock": True, "dim": "Exacerbating", "line": "the pain is worse when you breathe in or cough"}, 
# #                                        {"lock": True, "dim": "Relieving", "line": "the pain seems to be better when you are sitting up right rather than lying down"}], 
# #         "Associated Symptoms": [{"lock": False, "line": "You have felt warm in the past two days. When you took your temperature, it was 100.1 degrees F."}, 
# #                                 {"lock": False, "line": "You have been feeling very tired and just not well for the past 5 days."}, 
# #                                 {"lock": False, "line": "You occasionally feel like it can be difficult to breathe (because of the pain), especially when you lay back - it's better if you don't take deep breaths."}], 
# #         "Medical History": [{"lock": False, "line": "You had cold symptoms about three weeks ago (they're gone now). You thought it was the flu."}, 
# #                             {"lock": True, "line": "You have high cholesterol and take a statin for it."}, 
# #                             {"lock": False, "line": "You have been fully boosted for COVID, but do not always get a flu vaccine. Your last COVID booster was one year ago."}], 
# #         "Surgical History": [{"lock": False, "line": "N/A"}], 
# #         "Medications": [{"lock": False, "line": "If asked about medications, you will say Atorvastatin once a day, but you do not know the dose."}, 
# #                         {"lock": True, "line": "If asked about over-the-counter medications, say that you also take Vitamin D and a calcium supplement.  You have also recently started taking a pro-biotic."}], 
# #         "Allergies": [{"lock": False, "line": "You are very allergic to bees. Your lips and tongue swelled last time you were stung and you had to go to the Emergency Room- that was 15 years ago."}], 
# #         "Family History": [{"lock": False, "line": "Your father died suddenly of a heart attack when he was 50 years old."}, 
# #                            {"lock": False, "line": "Your mother was diagnosed with breast cancer two years ago."}], 
# #         "Social History": [{"lock": True, "line": "You have never smoked."}, 
# #                            {"lock": True, "line": "You drink about 1 glasses of wine or a cocktail during the week."}, 
# #                            {"lock": False, "line": "You live with your partner and you have two children together, ages 11 and 8."}, 
# #                            {"lock": False, "line": "You are a software engineer."}], 
# #         "Other Symptoms": [{"lock": False, "line": "N/A"}]}

# # diagnosis = {"Main": {"Acute pericarditis": 8}, 
# #              "Secondary": {"Acute pericarditis": 1, 
# #                            "Acute Coronary Syndrome (ACS)": 1, 
# #                            "Non-ST-elevation myocardial infarction (NSTEMI)": 1, 
# #                            "Unstable Angina": 1, 
# #                            "Aortic dissection": 1, 
# #                            "Gastroesophageal reflux disease (GERD)": 1, 
# #                            "Pulmonary embolism": 1, 
# #                            "Pneumonia": 1}}

# messages = [{"role": "User", "content": "Hello, I'm Dr. Corbett. What brings you in today?"},
#             {"role": "AI", "content": "Hi there, I've been having this sharp pain in my chest. It's been going on for about a day and a half now. It started off mild but it's gotten much worse today. I'm really worried because my dad died of a heart attack when he was 50."}, 
#             {"role": "User", "content": "Tell me more about this sharp pain in your chest"}, 
#             {"role": "AI", "content": "Well, it's right in the center of my chest. It's a stabbing kind of pain, really severe. I've never felt anything like this before. It's making me quite nervous, to be honest."}, 
#             {"role": "User", "content": "Any difficulty breathing?"}, 
#             {"role": "AI", "content": "Yes, sometimes it feels a bit hard to breathe, especially when I lay back. It's a bit better if I don't take deep breaths."}, 
#             {"role": "User", "content": "Do you have pain anywhere else?"}, 
#             {"role": "AI", "content": "Yes, I've also noticed some pain along the upper part of my back, on both shoulders."}, 
#             {"role": "User", "content": "Do you have high blood pressure or high cholesterol?"}, 
#             {"role": "AI", "content": "I do have high cholesterol, and I take a statin for it. But as far as I know, I don't have high blood pressure."}, 
#             {"role": "User", "content": "Are there any medical issues that run in your family?"}, 
#             {"role": "AI", "content": "Yes, my father died suddenly of a heart attack when he was 50 years old. And my mother was diagnosed with breast cancer two years ago."}, 
#             {"role": "User", "content": "Do you drink or smoke?"}, 
#             {"role": "AI", "content": "No, I've never smoked. I do enjoy a glass of wine or a cocktail during the week, but that's about it."}]

# # for message in messages:
# #     interview.add_message(Message("input" if message["role"] == "User" else "output", message["role"], message["content"]))
# # grading = {"data": patient.weights_data, 
# #            "diagnosis": diagnosis}

patient = Patient("Jackie Smith")
dict = patient.get_dict()

with open("./Patient_Info/JackieSmith.json", "w") as json_file:
    json.dump(dict, json_file, indent=2)