import json
import pydantic
from typing import Optional, List

from lookups import *


class Patient(pydantic.BaseModel):
    name: str
    case: Optional[dict]
    grading: Optional[dict]
    physical : Optional[str]
    ECG: Optional[str]
    explanation: Optional[str]
    convo_prompt: Optional[str]
    speech: Optional[dict]

    # Attributes
        # self.name = name            # str
        # self.case = None            # dict{str, list[dict{str, str/bool}]}
        # self.grading = None         # dict{str, dict{str, dict{str, int}}}
        # self.physical = None        # str path
        # self.ECG = None             # str path
        # self.convo_prompt = None    # str
        # self.speech = None          # dict{str, str}
    
    @classmethod
    def build(cls, name:str):
        
        with open(PATIENTS[name], "r") as json_file:
            JSON = json.load(json_file)

        # Create virtual patient prompt
        base = BASE_PROMPT.replace("{patient}", name)
        convo_prompt = str(base)
        case = JSON["case"]
        convo_prompt += cls.process_case(case)

        # Extract grading for patient
        grading = JSON["grading"]

        # Assign physical, ECG, explanation data paths for patient for website display use
        physical = JSON["physical"]
        ECG = JSON["ECG"]
        explanation = JSON["explanation"]

        # Extract speech settings
        speech = JSON["speech"]

        return cls(name=name, 
                   case=case, 
                   grading=grading, 
                   physical=physical, 
                   ECG=ECG, 
                   explanation=explanation,
                   convo_prompt=convo_prompt, 
                   speech=speech)

    @classmethod
    def process_case(cls, case: dict[str, list[dict[str]]]) -> str:
        case_prompt = ""
        for category in case:
            case_prompt += "[" + category + "] \n"
            if category == "Personal Details":
                for detail, desc in case[category].items():
                    case_prompt += detail + ": " + desc+ " \n"
            elif category == "Chief Concern":
                case_prompt += case[category] + " \n"
            elif category == "HIPI":
                for dim in case[category]:
                    line = dim + ": " + dim["desc"]
                    if dim["lock"]:
                        line = "<LOCKED> " + line
                    case_prompt += line + "\n"
            else:
                for element in case[category]:
                    line = element["desc"]
                    if element["lock"]:
                        line = "<LOCKED> " + line
                    case_prompt += line + " \n"
        
        # for category in case: 
        #     case_prompt += "[" + category + "] \n"
        #     if category == "Personal Details":
        #         for element in case[category]:
        #             case_prompt += element["detail"] + ": " + element["line"] + " \n"
        #     elif category == "Chief Concern":
        #         case_prompt += case[category] + " \n"
        #     elif category == "History of Present Illness":
        #         for element in case[category]:
        #             line = element["dim"] + ": " + element["line"]
        #             if element["lock"]:
        #                 line = "<LOCKED> " + line
        #             case_prompt += line + "\n"
        #     else:
        #         for element in case[category]:
        #             line = element["line"]
        #             if element["lock"]:
        #                 line = "<LOCKED> " + line
        #             case_prompt += line + " \n"
        return case_prompt

    # def get_dict(self):
    #     to_return = {"name": self.name, 
    #                  "case": self.case, 
    #                  "grading": self.grading, 
    #                  "physical": self.physical, 
    #                  "ECG": self.ECG}
    #     return to_return