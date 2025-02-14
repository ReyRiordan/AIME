from lookups import *
import json
from openai import OpenAI
import pydantic 
from typing import Optional, List

from .patient import *
from .message import *
from web_methods.LLM import *
            
class Feedback(pydantic.BaseModel):

    feedback: Optional[dict] = {}           # {type: {text: str, points: int}}

    @classmethod
    def build(cls, patient: Patient, messages: list[Message], post_note: dict[str, str]):

        # Import rubric bases
        with open("./Prompts/base_rubrics.json", "r", ) as json_file:
            BASE = json.load(json_file)

        # Initialize
        feedback = {"Key Findings": None,
                    "HPI": [], # 3
                    "Past Histories": [], # 2
                    "Summary": None,
                    "Assessment": [], # 3
                    "Plan": None}

        # Feedback and grading
        for category in ["Key Findings", "HPI", "Past Histories", "Summary", "Assessment", "Plan"]:
            if feedback[category] is not None:
                for p, d in BASE[category].items():
                    response = generate_feedback(title = d["title"],
                                                 desc = d["desc"],
                                                 rubric = patient.grading[category][p]["rubric"],
                                                 user_input = post_note[category])
                    # score = generate_score()
                    feedback[category].append({"text": response,
                                            #    "score": score,
                                               "max": patient.grading[category][p]["points"]})
            else:
                response = generate_feedback(title = BASE[category]["title"],
                                             desc = BASE[category]["desc"],
                                             rubric = patient.grading[category]["rubric"],
                                             user_input = post_note[category])
                # score = generate_score()
                feedback[category].append({"text": response,
                                        #    "score": score,
                                           "max": patient.grading[category]["points"]})

        return cls(feedback=feedback)

        # self.data_acquisition = DataAcquisition(patient, messages)
        # self.diagnosis = Diagnosis(patient, user_diagnosis)        
    
    

    
    # DEPRECATED get_dict() method

    # def get_dict(self):
    #     to_return = {"Data Acquisition": self.data_acquisition.get_dict(), 
    #                  "Diagnosis": self.diagnosis.get_dict()}
    #     return to_return