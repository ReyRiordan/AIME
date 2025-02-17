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
    def build(cls, patient: Patient, messages: list[Message], post_note_inputs: dict[str, str]):

        # Import rubric bases
        with open("./Prompts/base_rubrics.json", "r", ) as json_file:
            BASE = json.load(json_file)

        # Initialize
        feedback = {"Key Findings": None,
                    "HPI": {}, # 3
                    "Past Histories": {}, # 2
                    "Summary": None,
                    "Assessment": {}, # 3
                    "Plan": None}

        # Feedback and grading
        for category in ["Key Findings", "HPI", "Past Histories", "Summary", "Assessment", "Plan"]:
            if feedback[category] is not None:
                for part, content in BASE[category].items():
                    response = generate_feedback(title = content["title"],
                                                 desc = content["desc"],
                                                 rubric = patient.grading[category][part]["rubric"],
                                                 user_input = post_note_inputs[category])
                    split_attempt = response.strip().split("Thought process:")
                    if len(split_attempt) == 2:
                        comment, scoring = split_attempt
                        thought, score = scoring.split("FINAL SCORE: ")
                        score = int(score)
                    else:
                        comment = response
                        thought = None
                        score = 0
                    feedback[category][part] = {"title": content["title"],
                                                "desc": content["desc"],
                                                "rubric": patient.grading[category][part]["rubric"],
                                                "input": post_note_inputs[category],
                                                "comment": comment,
                                                "thought": thought,
                                                "score": score,
                                                "max": patient.grading[category][part]["points"]}
                    # score = generate_score(feedback[category][part])
            else:
                response = generate_feedback(title = BASE[category]["title"],
                                             desc = BASE[category]["desc"],
                                             rubric = patient.grading[category]["rubric"],
                                             user_input = post_note_inputs[category])
                split_attempt = response.strip().split("Thought process:")
                if len(split_attempt) == 2:
                    comment, scoring = split_attempt
                    thought, score = scoring.split("FINAL SCORE: ")
                    score = int(score)
                else:
                    comment = response
                    thought = None
                    score = 0
                feedback[category] = {"title": BASE[category]["title"],
                                      "desc": BASE[category]["desc"],
                                      "rubric": patient.grading[category]["rubric"],
                                      "input": post_note_inputs[category],
                                      "comment": comment,
                                      "thought": thought,
                                      "score": score,
                                      "max": patient.grading[category]["points"]}

        return cls(feedback=feedback)

        # self.data_acquisition = DataAcquisition(patient, messages)
        # self.diagnosis = Diagnosis(patient, user_diagnosis)        
    
    

    
    # DEPRECATED get_dict() method

    # def get_dict(self):
    #     to_return = {"Data Acquisition": self.data_acquisition.get_dict(), 
    #                  "Diagnosis": self.diagnosis.get_dict()}
    #     return to_return