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
    def build(cls, patient: Patient, messages: list[Message], post_note_inputs: dict[str, str], rubric_id=RUBRIC_ID):
        info = {
            'rubric_id': rubric_id, 
            'model': {
                'name': FEEDBACK_MODEL, 
                'temperature': FEEDBACK_TEMP, 
                'token_cost': COSTS[FEEDBACK_MODEL]
                }, 
            'tokens': {
                'input': 0, 
                'output': 0
            }
        }
        post_note = {}

        # Initialize
        # if short:
        #     categories = ["Summary Statement", "Assessment", "Plan"]
        # else:
        #     categories = ["Key Findings", "HPI", "Past Histories", "Summary Statement", "Assessment", "Plan"]
        categories = ["Summary Statement", "Assessment", "Plan"]
        sectioned = ["HPI", "Past Histories", "Assessment"]

        # Use info from source rubric + user input to generate/process/write feedback for specific section/part
        def generate_process_write(source: dict, input: str):
            response = generate_feedback(title = source["title"],
                                         desc = source["desc"],
                                         rubric = source["rubric"],
                                         user_input = input, 
                                         tokens = info['tokens'])
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
            output = {"input": input,
                      "comment": comment,
                      "thought": thought,
                      "score": score,
                      "max": source["points"]}
            return output

        # Create feedback
        for category in categories:
            if category in sectioned:
                post_note[category] = {}
                for part, content in RUBRIC[category].items():
                    post_note[category][part] = generate_process_write(content, post_note_inputs[category])
            else:
                post_note[category] = generate_process_write(RUBRIC[category], post_note_inputs[category])
                
            st.write(f"Section \"{category}\" complete.")

        
        return cls(info=info, post_note=post_note)

        # self.data_acquisition = DataAcquisition(patient, messages)
        # self.diagnosis = Diagnosis(patient, user_diagnosis)