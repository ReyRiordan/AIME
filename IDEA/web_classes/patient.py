import json
import pydantic
from typing import Optional, List

from lookups import *


class Patient(pydantic.BaseModel):
    id: str
    case: Optional[dict]
    # grading: Optional[dict]
    physical : Optional[str]
    # ECG: Optional[str]
    explanation: Optional[str]
    convo_prompt: Optional[str]
    speech: Optional[dict]
    # label_descs: Optional[dict]

    # Attributes
        # self.name = name            # str
        # self.case = None            # dict{str, list[dict{str, str/bool}]}
        # self.grading = None         # dict{str, dict{str, dict{str, int}}}
        # self.physical = None        # str path
        # self.ECG = None             # str path
        # self.convo_prompt = None    # str
        # self.speech = None          # dict{str, str}
        # self.label_descs = None     # dict{str, str}
    
    @classmethod
    def build(cls, id: str):
        
        with open("./Patient_Info/" + id.replace(" ", "") + ".json", "r") as json_file:
            JSON = json.load(json_file)

        # Create virtual patient prompt
        base = BASE_PROMPT.replace("{patient}", id)
        convo_prompt = str(base)
        case = JSON["Case"]
        convo_prompt += cls.process_case(case)

        # # Extract grading for patient
        # grading = JSON["Grading"]
        # if isinstance(grading, str):
        #     with open(grading, "r") as grading_file:
        #         grading = json.load(grading_file)

        # Assets (hardcoded for now)
        #TODO flexible assets
        physical = JSON["Assets"]["Physical Examination"]
        # ECG = JSON["Assets"]["ECG"]
        explanation = JSON["Assets"]["Case Explanation"]

        # Extract speech settings
        speech = JSON["Speech"]

        # Extract label descriptions (static + patient dependent)
        # with open(PATHS["Static Label Descriptions"], "r") as label_descs_json:
        #     label_descs = json.loads(label_descs_json.read())
        # for label, desc in JSON["Labels"].items():
        #     label_descs[label] = desc

        return cls(id=id, 
                   speech=speech,
                   physical=physical, 
                #    ECG=ECG, 
                   explanation=explanation, 
                   case=case, 
                #    grading=grading, 
                   convo_prompt=convo_prompt, 
                #    label_descs=label_descs
                )

    @classmethod
    def process_case(cls, case: dict[str, list[dict[str]]]) -> str:
        case_prompt = ""
        for category in case:
            case_prompt += "[" + category + "] \n"
            if category == "Personal Details":
                for detail, desc in case[category].items():
                    case_prompt += detail + ": " + desc+ " \n"
            elif category == "Background":
                case_prompt += case[category] + " \n"
            elif category == "HIPI":
                for bullet in case[category]:
                    line = bullet["desc"]
                    if bullet["lock"]:
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