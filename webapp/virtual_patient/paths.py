BASE_PATH = "./Prompts/Base_1-15.txt"
ASOC_PATH = "./Prompts/asoc_descriptions.txt"
RISK_PATH = "./Prompts/risk_descriptions.txt"
CLASS_ASOC_PATH = "./Prompts/Class_asoc_2-8.txt"
CLASS_RISK_PATH = "./Prompts/Class_risk_2-8.txt"

cases = {
    "John Smith" : ["./Prompts/JohnSmith_1-15.txt", "./Prompts/JohnSmith_asoc.txt", "./Prompts/JohnSmith_risk.txt"], 
    "Jackie Smith" : ["./Prompts/JackieSmith_1-15.txt", "./Prompts/JackieSmith_asoc.txt", "./Prompts/JackieSmith_risk.txt"]
}

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
                "Drug Use": 2} # note "Other" is ommitted
# Employment 1, Social_Support 1

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