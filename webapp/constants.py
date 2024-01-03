# PAGE INFORMATION
LOGIN_PAGE = 0
PATIENT_SELECTION = 1
PATIENT_LOADING = 2
CHAT_INTERFACE = 3
CREATE_INTERVIEW_FILE = 4
POST_INTERVIEW = 5
PHYSICAL_SCREEN = 6
ECG_SCREEN = 7
FEEDBACK_SCREEN = 8
FINAL_SCREEN = 9

# FILE LOCATIONS
PHYSICAL_LOCATION_JOHN = "./Patient_Info/Physical_JohnSmith.docx"
ECG_LOCATION_JOHN = "./Patient_Info/ECG_JohnSmith.png"
PHYSICAL_LOCATION_JACKIE = "./Patient_Info/Physical_Jackie.docx"
ECG_LOCATION_JACKIE="./Patient_Info/ECG_Jackie.jpg"

BASE_PROMPT = "./Prompt/Base_12-11.txt"
prompts = {
    "John Smith" : "./Prompt/JohnSmith_12-11.txt",
    "Jackie Smith" : "./Prompt/JackieSmith_12-11.txt"
}

# EMAIL API
EMAILS_TO_SEND = [('rutgers.aime@gmail.com')]