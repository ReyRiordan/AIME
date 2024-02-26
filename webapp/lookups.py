# Streamlit stages
LOGIN_PAGE = 0
SETTINGS = 1
CHAT_SETUP = 2
CHAT_INTERFACE_TEXT = 3
CHAT_INTERFACE_VOICE = 4
POST_INTERVIEW = 5
PHYSICAL_SCREEN = 6
ECG_SCREEN = 7
DIAGNOSIS = 11
FEEDBACK_SETUP = 8
FEEDBACK_SCREEN = 9
FINAL_SCREEN = 10

# LLM related
CONVO_MODEL = "gpt-4"
CLASS_MODEL = "gpt-4"
CHAT_TEMP = 0.7

SUM_MODEL = "gpt-3.5-turbo-0125"
with open("./Prompts/Summarizer_2-25.txt", "r", encoding="utf8") as summarizer_file:
    SUM_PROMPT = summarizer_file.read()
SUM_TEMP = 0.0

DIAG_MODEL = "gpt-3.5-turbo-0125"
with open("./Prompts/Diagnosis_Grader_2-25.txt", "r", encoding="utf8") as grader_file:
    DIAG_PROMPT = grader_file.read()
DIAG_TEMP = 0.0

# Email API
EMAIL_TO_SEND = [('rutgers.aime@gmail.com')]

# Classification base prompts
CLASS_INPUT = "./Prompts/Class_Input_2-13.txt"
CLASS_OUTPUT = "./Prompts/Class_Output_2-13.txt"

PATIENTS = {
    "John Smith": {"base": "./Prompts/Base_2-23.txt", 
                   "case": "./Patient_Info/JohnSmith_case.json", 
                   "grading": "./Patient_Info/JohnSmith_grading.json", 
                   "physical": "./Patient_Info/JohnSmith_physical.docx", 
                   "ECG": "./Patient_Info/JohnSmith_ECG.png"}, 
    "Jackie Smith": {"base": "./Prompts/Base_2-23.txt", 
                     "case": "./Patient_Info/JackieSmith_case.json", 
                     "grading": "./Patient_Info/JackieSmith_grading.json", 
                     "physical": "./Patient_Info/JackieSmith_physical.docx", 
                     "ECG": "./Patient_Info/JackieSmith_ECG.png"}
}

CATEGORIES = {
    "gen": {"tab": "data", 
            "type": "input", 
            "header": "General Questions", 
            "color": "blue", 
            "highlight": "#bae1ff", # light blue
            "desc": "./Prompts/desc_gen.json"}, 
    "dims": {"tab": "data", 
             "type": "output", 
             "header": "Dimensions of Chief Concern", 
             "color": "red", 
             "highlight": "#ffb3ba", # light red
             "desc": "./Prompts/desc_dims.json"}, 
    "asoc": {"tab": "data", 
             "type": "input", 
             "header": "Associated Symptoms Questions", 
             "color": "orange", 
             "highlight": "#ffdfba", # light orange
             "desc": "./Prompts/desc_asoc.json"}, 
    "risk": {"tab": "data", 
             "type": "input", 
             "header": "Risk Factor Questions", 
             "color": "violet", 
             "highlight": "#f1cbff", # light violet
             "desc": "./Prompts/desc_risk.json"}
}

WEBSITE_TEXT = {
        "intro" : "./webapp/website_text/intro.txt",
        "selection" : "./webapp/website_text/selection.txt",
        "interview" : "./webapp/website_text/interview.txt",
        "post" : "./webapp/website_text/post.txt",
        "feedback" : "./webapp/website_text/feedback.txt",
        "final": "./webapp/website_text/final.txt"
}