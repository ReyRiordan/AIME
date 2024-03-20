import json

from lookups import *


class Patient:

    def __init__(self, name):
        # Attributes
        self.name = name            # str
        self.case = None            # dict{str, list[dict{str, str/bool}]}
        self.grading = None         # dict{str, dict{str, dict{str, int}}}
        self.physical = None        # str path
        self.ECG = None             # str path
        self.convo_prompt = None    # str
        self.speech = None          # dict{str, str}

        with open(PATIENTS[name], "r") as json_file:
            JSON = json.load(json_file)

        # Create virtual patient prompt
        with open(JSON["prompt"]["file"], "r") as base_file:
            base = base_file.read()
        base = base.replace("{patient}", name)
        self.convo_prompt = str(base)
        self.case = JSON["case"]
        self.convo_prompt += self.process_case(self.case)

        # Extract grading for patient
        self.grading = JSON["grading"]

        # Assign physical and ECG data paths for patient for website display use
        self.physical = JSON["physical"]
        self.ECG = JSON["ECG"]

        # Extract speech settings
        self.speech = JSON["speech"]


    def process_case(self, case: dict[str, list[dict[str]]]) -> str:
        case_prompt = ""
        for category in case: 
            case_prompt += "[" + category + "] \n"
            if category == "Personal Details":
                for element in case[category]:
                    case_prompt += element["detail"] + ": " + element["line"] + " \n"
            elif category == "Chief Concern":
                case_prompt += case[category] + " \n"
            elif category == "History of Present Illness":
                for element in case[category]:
                    line = element["dim"] + ": " + element["line"]
                    if element["lock"]:
                        line = "<LOCKED> " + line
                    case_prompt += line + "\n"
            else:
                for element in case[category]:
                    line = element["line"]
                    if element["lock"]:
                        line = "<LOCKED> " + line
                    case_prompt += line + " \n"
        return case_prompt

    def get_dict(self):
        to_return = {"name": self.name, 
                     "case": self.case, 
                     "grading": self.grading, 
                     "physical": self.physical, 
                     "ECG": self.ECG}
        return to_return