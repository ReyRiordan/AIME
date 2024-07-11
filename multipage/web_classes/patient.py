import json
import pydantic
from typing import Optional, List

from lookups import *


class Patient(pydantic.BaseModel):
    id: str
    case: Optional[dict]
    grading: Optional[dict]
    physical : Optional[str]
    ECG: Optional[str]
    explanation: Optional[str]
    convo_prompt: Optional[str]
    speech: Optional[dict]
    labels: Optional[dict]

    # Attributes
        # self.name = name            # str
        # self.case = None            # dict{str, list[dict{str, str/bool}]}
        # self.grading = None         # dict{str, dict{str, dict{str, int}}}
        # self.physical = None        # str path
        # self.ECG = None             # str path
        # self.convo_prompt = None    # str
        # self.speech = None          # dict{str, str}
        # self.labels = None          # dict{str, str}
    
    @classmethod
    def build(cls, id: str):
        
        with open(PATIENTS[id], "r") as json_file:
            JSON = json.load(json_file)

        # Create virtual patient prompt
        base = BASE_PROMPT.replace("{patient}", id)
        convo_prompt = str(base)
        case = JSON["Case"]
        convo_prompt += cls.process_case(case)

        # Extract grading for patient
        grading = JSON["Grading"]

        # Assets (hardcoded for now)
        #TODO flexible assets
        physical = JSON["Assets"]["Physical Examination"]
        ECG = JSON["Assets"]["ECG"]
        explanation = JSON["Assets"]["Case Explanation"]

        # Extract speech settings
        speech = JSON["Speech"]

        # Extract patient dependent label descriptions
        labels = JSON["Labels"]

        return cls(id=id, 
                   speech=speech,
                   physical=physical, 
                   ECG=ECG, 
                   explanation=explanation, 
                   case=case, 
                   grading=grading, 
                   convo_prompt=convo_prompt, 
                   labels=labels)

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