# PAGE INFORMATION
LOGIN_PAGE = 0
SETTINGS = 1
CHAT_SETUP = 2
CHAT_INTERFACE_TEXT = 3
CHAT_INTERFACE_VOICE = 4
POST_INTERVIEW = 5
PHYSICAL_SCREEN = 6
ECG_SCREEN = 7
FEEDBACK_SETUP = 8
FEEDBACK_SCREEN = 9
FINAL_SCREEN = 10

# GPT
MODEL = "gpt-4"

# EMAIL API
EMAIL_TO_SEND = [('rutgers.aime@gmail.com')]

# Classification related
CLASSIFY_GEN_PROMPT = "./Prompts/Class_gen_2-7.txt"
WEIGHTS_GEN = {"Introduction" : 5, 
                "Confirm Identity" : 5, 
                "Establish Chief Concern" : 5, 
                "Additional Information" : 5, 
                "Medical History": 5, 
                "Surgery Hospitalization": 5, 
                "Medication": 5, 
                "Allergies": 5, 
                "Family History": 5, 
                "Alcohol": 2, 
                "Smoking": 2, 
                "Drug Use": 2,
                "Other" : 0} 

# Employment 1, Social_Support 1
CLASSIFY_DIMS_PROMPT = "./Prompts/Class_dims_2-8.txt"
WEIGHTS_DIMS = {"Onset": 5, 
                  "Quality": 5, 
                  "Location": 5, 
                  "Timing": 5, 
                  "Pattern": 5, 
                  "Exacerbating": 5, 
                  "Relieving": 5, 
                  "Prior_History": 5, 
                  "Radiation": 5, 
                  "Severity": 5} # "Other" ommitted