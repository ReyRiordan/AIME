from lookups import *
import json
from openai import OpenAI
import pydantic 
from typing import Optional, List

from .patient import *
from .message import *
from web_methods.LLM import *
            
class Feedback(pydantic.BaseModel):

    info: Optional[dict]
    post_note: Optional[dict]

    @classmethod
    def restore_previous(cls, feedback: dict):
        return cls(feedback=feedback)
    
    @classmethod
    def build(cls, short: bool, patient: Patient, messages: list[Message], post_note_inputs: dict[str, str], rubric_id=RUBRIC_ID):
        info = {'rubric_id': rubric_id, 
                'model': FEEDBACK_MODEL, 
                'temperature': FEEDBACK_TEMP, 
                'token_cost': COSTS[FEEDBACK_MODEL]}
        post_note = {}

        # Initialize
        if short:
            categories = ["Summary Statement", "Assessment", "Plan"]
        else:
            categories = ["Key Findings", "HPI", "Past Histories", "Summary Statement", "Assessment", "Plan"]
        sectioned = ["HPI", "Past Histories", "Assessment"]

        # Post note
        for category in categories:
            # categories with multiple parts
            if category in sectioned:
                post_note[category] = {}
                # for each part
                for part, content in RUBRIC[category].items():
                    # get LLM output
                    response = generate_feedback(title = content["title"],
                                                 desc = content["desc"],
                                                 rubric = content["rubric"],
                                                 user_input = post_note_inputs[category])
                    # split into feedback / thought process + final score
                    split_attempt = response.strip().split("Thought process:")
                    if len(split_attempt) == 2:
                        comment, scoring = split_attempt
                        # split into thought process / final score
                        thought, score = scoring.split("FINAL SCORE: ")
                        score = int(score)
                    else: # error handling?
                        comment = response
                        thought = None
                        score = 0
                    post_note[category][part] = {"input": post_note_inputs[category],
                                                "comment": comment,
                                                "thought": thought,
                                                "score": score,
                                                "max": patient.grading[category][part]["points"]}
            # categories without multiple parts
            else:
                response = generate_feedback(title = RUBRIC[category]["title"],
                                             desc = RUBRIC[category]["desc"],
                                             rubric = RUBRIC[category]["rubric"],
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
                post_note[category] = {"input": post_note_inputs[category],
                                      "comment": comment,
                                      "thought": thought,
                                      "score": score,
                                      "max": patient.grading[category]["points"]}
            
            st.write(f"Section \"{category}\" complete.")

        return cls(info=info, post_note=post_note)

        # self.data_acquisition = DataAcquisition(patient, messages)
        # self.diagnosis = Diagnosis(patient, user_diagnosis)        
    
    

    
    # DEPRECATED get_dict() method

    # def get_dict(self):
    #     to_return = {"Data Acquisition": self.data_acquisition.get_dict(), 
    #                  "Diagnosis": self.diagnosis.get_dict()}
    #     return to_return