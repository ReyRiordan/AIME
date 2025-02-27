from lookups import *
import json
from openai import OpenAI
import datetime as date
import pydantic 
from typing import Optional, List

from .patient import *
from .message import *
from .feedback import *

class Interview(pydantic.BaseModel):
    id : Optional[int] = None
    start_time : Optional[str] = None
    time_elapsed : Optional[str] = None
    cost : Optional[int] = None
    username : str                                  # str
    patient : Patient                               # Patient
    messages : Optional[List[Message]] = []         # list[Message]
    post_note_inputs : Optional[dict] = {}                 # dict{str, str/list[str]}
    feedback : Optional[Feedback] = None            # Feedback
    survey : Optional[dict] = None
    
    @classmethod
    def build(cls, username: str, patient: Patient):
        #Attributes
        # messages = []            # list[Message]
        # user_diagnosis = None     # dict{str, str/list[str]}
        # feedback = None          # Feedback

        return cls(username=username, patient=patient) 
            
    def add_feedback(self):
        self.feedback = Feedback.build(patient=self.patient, messages=self.messages, post_note_inputs=self.post_note_inputs)
    
    def add_key_findings(self, findings: str):
        self.post_note_inputs["Key Findings"] = findings

    def add_other_inputs(self, hpi: str, past_histories: str, summary: str, assessment: str, plan: str):
        self.post_note_inputs["HPI"] = hpi
        self.post_note_inputs["Past Histories"] = past_histories
        self.post_note_inputs["Summary Statement"] = summary
        self.post_note_inputs["Assessment"] = assessment
        self.post_note_inputs["Plan"] = plan
    
    def add_message(self, message: Message) -> None:
        if message.type and message.role and message.content:
            self.messages.append(message)

    # DEPRECATED get_dict() method
    # Will keep around for a week in case something breaks
    # 
    # def get_dict(self):
    #     to_return = {"start_time": self.start_time,
    #                  "time_elapsed": self.time_elapsed,
    #                  "cost": self.cost,
    #                  "username": self.username, 
    #                  "patient": self.patient.get_dict(), 
    #                  "messages": [message.get_dict() for message in self.messages], 
    #                  "diagnosis_inputs": self.diagnosis_inputs if self.diagnosis_inputs else None, 
    #                  "feedback": self.feedback.get_dict() if self.feedback else None,
    #                  "survey": self.survey if self.survey else None}
    #     return to_return

    def get_json(self):
        return json.dumps(self.get_dict(),indent=4)