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
DB_URI = os.getenv("DB_URI")
DB_NAME = "TESTING"
# DATABASE_USERNAME=os.getenv("DB_USERNAME")
# DATABASE_PASSWORD=os.getenv("DB_PASSWORD")

# Email API
EMAIL_TO_SEND = [('rutgers.aime@gmail.com')]


# Streamlit stages
CLOSED = -1
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
KEY_PHYSICALS = 14
VIEW_INTERVIEWS_ADMIN = 15

COSTS = {"gpt-4o": {"input": 5, "output": 15},
         "gpt-4-turbo": {"input": 10, "output": 30},
         "gpt-4": {"input": 30, "output": 60},
         "gpt-3.5-turbo-0125": {"input": 0.5, "output": 1.5},
         "claude-3-7-sonnet-latest": {"input": 3, "output": 15}}

# Audio related
STT = OpenAI()
STT_MODEL = "gpt-4o-mini-transcribe"
TTS = OpenAI()
TTS_MODEL = "tts-1"
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

FEEDBACK_CLIENT = Anthropic()
FEEDBACK_MODEL = "claude-3-7-sonnet-latest"
FEEDBACK_TEMP = 0.0

CLASS_CLIENT = Anthropic()
CLASS_MODEL = "claude-3-7-sonnet-latest"
CLASS_TEMP = 0.0
DIAG_CLIENT = OpenAI()
DIAG_MODEL = "gpt-4-turbo"
DIAG_TEMP = 0.0


# Paths for prompt files
PATHS = {"Patient Base": "./Prompts/Base_3-27.txt",
         "Convo Summarizer": "./Prompts/Summarizer_4-22.txt",
         "Static Label Descriptions": "./Prompts/label_descs.json",
         "Label Examples": "./Prompts/datacategory_examples.json",
         "Input Classification": "./Prompts/Grade_DataIn_4-14.txt",
         "Output Classification": "./Prompts/Grade_DataOut_4-14.txt",
         "Grade Summary": "./Prompts/Grade_Sum_4-14.txt",
         "Grade Rationale": "./Prompts/Grade_Rat_6-26.txt",
         "Grade Diagnosis": "./Prompts/Grade_Diag_4-23.txt",
         "Feedback": "./Prompts/Feedback_2-17.txt"}


# Assignments
with open("./IDEA/assignments/M1.json", "r") as assignments_file:
    ASSIGNMENTS = json.load(assignments_file)


# Convo related
with open(PATHS["Patient Base"], "r", encoding="utf8") as base_file:
    BASE_PROMPT = base_file.read()
with open(PATHS["Convo Summarizer"], "r", encoding="utf8") as summarizer_file:
    SUM_PROMPT = summarizer_file.read()
with open(PATHS["Feedback"], "r", encoding="utf8") as feedback_file:
    FEEDBACK_PROMPT = feedback_file.read()
MAX_MEMORY = 12 # no limit rn


# Grading related
BATCH_MAX = 20
BATCH_DELAY = 60

with open(PATHS["Label Examples"], "r") as cat_examples_json:
    LABEL_EXAMPLES = json.loads(cat_examples_json.read())
CLASS_INPUT = PATHS["Input Classification"]
CLASS_OUTPUT = PATHS["Output Classification"]

with open(PATHS["Grade Summary"], "r", encoding="utf8") as grade_sum_file:
    GRADE_SUM_PROMPT = grade_sum_file.read()
with open(PATHS["Grade Rationale"], "r", encoding="utf8") as grade_rat_file:
    GRADE_RAT_PROMPT = grade_rat_file.read()
with open(PATHS["Grade Diagnosis"], "r", encoding="utf8") as grade_diag_file:
    GRADE_DIAG_PROMPT = grade_diag_file.read()