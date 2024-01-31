# PAGE INFORMATION
LOGIN_PAGE = 0
SETTINGS = 1
CHAT_SETUP = 2
CHAT_INTERFACE_TEXT = 3
CHAT_INTERFACE_VOICE = 4
POST_INTERVIEW = 5
PHYSICAL_SCREEN = 6
ECG_SCREEN = 7
FEEDBACK_SCREEN = 8
FINAL_SCREEN = 9

# GPT
MODEL = "gpt-4"

# EMAIL API
EMAIL_TO_SEND = [('rutgers.aime@gmail.com')]

# Classification related
CLASSIFY_INPUT_PROMPT = "./Prompts/Classification_1-29.txt"
CLASSIFY_INPUT_LABELS = ["Introduction",
                  "Confirm_Identity",
                  "Establish_Chief_Concern",
                  "Additional_Information",
                  "Medical_History",
                  "Surgery_Hospitalization",
                  "Medication",
                  "Allergies",
                  "Family_History",
                  "Alcohol",
                  "Smoking",
                  "Drug_Use"] # note "Other" is ommitted