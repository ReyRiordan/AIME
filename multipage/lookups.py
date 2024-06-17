import os
import streamlit as st
from openai import OpenAI
from anthropic import Anthropic
import json

# from dotenv import load_dotenv

# load_dotenv()

# if "lookups" not in st.session_state:
#     st.session_state.lookups = {
#         "LOGIN_PASS": os.getenv("LOGIN_PASS"), 
#         "DB_URI": os.getenv("DB_URI"), 
#         "DATABASE_USERNAME": os.getenv("DATABASE_USERNAME"), 
#         "DATABASE_PASSWORD": os.getenv("DATABASE_PASSWORD"), 
#         "EMAIL_TO_SEND": [('rutgers.aime@gmail.com')], 
#         "CLIENT": }

# SECRETS
LOGIN_PASS = os.getenv("LOGIN_PASS")
DB_URI=os.getenv("DB_URI")
DATABASE_USERNAME=os.getenv("DATABASE_USERNAME")
DATABASE_PASSWORD=os.getenv("DATABASE_PASSWORD")

# Email API
EMAIL_TO_SEND = [('rutgers.aime@gmail.com')]


# Streamlit stages
LOGIN_PAGE = 0
SETTINGS = 1
CHAT_SETUP = 2
CHAT_INTERFACE_TEXT = 3
CHAT_INTERFACE_VOICE = 4
POST_INTERVIEW = 5
PHYSICAL_ECG_SCREEN = 7
DIAGNOSIS = 8
FEEDBACK_SETUP = 9
FEEDBACK_SCREEN = 10
FINAL_SCREEN = 11
VIEW_INTERVIEWS = 12
SURVEY = 13

COSTS = {"gpt-4o": {"input": 5, "output": 15},
         "gpt-4-turbo": {"input": 10, "output": 30},
         "gpt-4": {"input": 30, "output": 60},
         "gpt-3.5-turbo-0125": {"input": 0.5, "output": 1.5}}

# Audio related
STT = OpenAI()
STT_MODEL = "whisper-1"
TTS = OpenAI()
# TTS_MODEL = "tts-1"
# AUDIO_OUT = ElevenLabs()


# LLM related

# CHAT_CLIENT = Anthropic()
# CONVO_MODEL = "claude-3-sonnet-20240229"
# CONVO_TEMP = 0.5
# SUM_MODEL = "claude-3-sonnet-20240229"
# SUM_TEMP = 0.0
CHAT_CLIENT = OpenAI()
CONVO_MODEL = "gpt-4o"
CONVO_TEMP = 0.7
SUM_MODEL = "gpt-4o"
SUM_TEMP = 0.0

GRADE_CLIENT = OpenAI()
CLASS_MODEL = "gpt-4"
CLASS_TEMP = 0.0
DIAG_MODEL = "gpt-4-turbo"
DIAG_TEMP = 0.0


# Convo related
with open("./Prompts/Base_5-16.txt", "r", encoding="utf8") as base_file:
    BASE_PROMPT = base_file.read()
with open("./Prompts/Summarizer_4-22.txt", "r", encoding="utf8") as summarizer_file:
    SUM_PROMPT = summarizer_file.read()
MAX_MEMORY = 12 # no limit rn


# Grading related
BATCH_MAX = 20
BATCH_DELAY = 30

with open("./Prompts/label_descs.json", "r") as label_descs_json:
    LABEL_DESCS = json.loads(label_descs_json.read())
with open("./Prompts/datacategory_examples.json", "r") as cat_examples_json:
    LABEL_EXAMPLES = json.loads(cat_examples_json.read())
CLASS_INPUT = "./Prompts/Grade_DataIn_4-14.txt"
CLASS_OUTPUT = "./Prompts/Grade_DataOut_4-14.txt"

with open("./Prompts/Grade_Sum_4-14.txt", "r", encoding="utf8") as grade_sum_file:
    GRADE_SUM_PROMPT = grade_sum_file.read()
with open("./Prompts/Grade_Rat_4-14.txt", "r", encoding="utf8") as grade_rat_file:
    GRADE_RAT_PROMPT = grade_rat_file.read()
with open("./Prompts/Grade_Diag_4-23.txt", "r", encoding="utf8") as grade_diag_file:
    GRADE_DIAG_PROMPT = grade_diag_file.read()


PATIENTS = {
    "John Smith": "./Patient_Info/JohnSmith.json", 
    "Jackie Smith": "./Patient_Info/JackieSmith.json"
}

DATACATEGORIES = {
    "gen": {"type": "input", 
            "header": "General Questions", 
            "color": "blue", 
            "highlight": "#bae1ff", # light blue
            "desc": "./Prompts/desc_gen.json"}, 
    "dims": {"type": "output", 
             "header": "Dimensions of Chief Concern", 
             "color": "red", 
             "highlight": "#ffb3ba", # light red
             "desc": "./Prompts/desc_dims.json"}, 
    "asoc": {"type": "input", 
             "header": "Associated Symptoms Questions", 
             "color": "orange", 
             "highlight": "#ffdfba", # light orange
             "desc": "./Prompts/desc_asoc.json"}, 
    "risk": {"type": "input", 
             "header": "Risk Factor Questions", 
             "color": "violet", 
             "highlight": "#f1cbff", # light violet
             "desc": "./Prompts/desc_risk.json"}
}

# WEBSITE_TEXT = {
#         "intro" : "./webapp/website_text/intro.txt",
#         "selection" : "./webapp/website_text/selection.txt",
#         "interview" : "./webapp/website_text/interview.txt",
#         "post" : "./webapp/website_text/post.txt",
#         "feedback" : "./webapp/website_text/feedback.txt",
#         "final": "./webapp/website_text/final.txt"
# }