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

# LLM models
CONVO_MODEL = "gpt-4"
CLASS_MODEL = "gpt-4"

# Email API
EMAIL_TO_SEND = [('rutgers.aime@gmail.com')]

# Classification base prompts
CLASS_INPUT = "./Prompts/Class_Input_2-13.txt"
CLASS_OUTPUT = "./Prompts/Class_Output_2-13.txt"

PATIENTS = {
    "John Smith": {"base": "./Prompts/Base_1-15.txt", 
                   "case": "./Prompts/JohnSmith_1-15.txt", 
                   "weights": "./Prompts/JohnSmith_weights.txt", 
                   "physical": "./Patient_Info/JohnSmith_physical.docx", 
                   "ECG": "./Patient_Info/JohnSmith_ECG.png"}, 
    "Jackie Smith": {"base": "./Prompts/Base_1-15.txt", 
                     "case": "./Prompts/JackieSmith_1-15.txt", 
                     "weights": "./Prompts/JackieSmith_weights.txt", 
                     "physical": "./Patient_Info/JackieSmith_physical.docx", 
                     "ECG": "./Patient_Info/JackieSmith_ECG.png"}
}

CATEGORIES = {
    "gen": {"tab": "data", 
            "type": "input", 
            "header": "General Questions", 
            "color": "blue", 
            "highlight": "#bae1ff", # light blue
            "desc_path": "./Prompts/label_desc_gen.txt"}, 
    "dims": {"tab": "data", 
             "type": "output", 
             "header": "Dimensions of Chief Concern", 
             "color": "red", 
             "highlight": "#ffb3ba", # light red
             "desc_path": "./Prompts/label_desc_dims.txt"}, 
    "asoc": {"tab": "data", 
             "type": "input", 
             "header": "Associated Symptoms Questions", 
             "color": "orange", 
             "highlight": "#ffdfba", # light orange
             "desc_path": "./Prompts/label_desc_asoc.txt"}, 
    "risk": {"tab": "data", 
             "type": "input", 
             "header": "Risk Factor Questions", 
             "color": "violet", 
             "highlight": "#f1cbff", # light violet
             "desc_path": "./Prompts/label_desc_risk.txt"}
}

WEBSITE_TEXT = {
        "intro" : "./webapp/website_text/intro.txt",
        "selection" : "./webapp/website_text/selection.txt",
        "interview" : "./webapp/website_text/interview.txt",
        "post" : "./webapp/website_text/post.txt",
        "feedback" : "./webapp/website_text/feedback.txt",
        "final": "./webapp/website_text/final.txt"
}