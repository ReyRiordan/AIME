from lookups import *
import json
from openai import OpenAI
from datetime import datetime
import pydantic 
from typing import Optional, List

from .patient import *
from .message import *
from .feedback import *

class Interview(pydantic.BaseModel):
    username : str
    patient : Patient
    start_time : Optional[str] = None
    finished : Optional[bool] = False
    times : Optional[dict] = {}
    tokens : Optional[dict] = None
    chat_mode : Optional[str] = None
    messages : Optional[List[Message]] = []
    post_note_inputs : Optional[dict] = {}
    feedback : Optional[Feedback] = None
    survey : Optional[str] = None
    convo_data : Optional[dict] = None
    
    @classmethod
    def restore_previous(cls, previous: dict):
        # messages = []
        # for message in previous["messages"]:
        #     messages.append(Message(type=message["type"], role=message["role"], content=message["content"]))
            
        return cls(username=previous["username"], 
                   patient=Patient.build(previous["patient"]["id"]), 
                   start_time=previous["start_time"], 
                   finished=previous["finished"], 
                   times=previous["times"], 
                   tokens=previous["tokens"], 
                   chat_mode=previous["chat_mode"], 
                #    messages=messages, 
                #    post_note_inputs=previous["post_note_inputs"], 
                #    feedback=Feedback.restore_previous(previous["feedback"]), 
                   survey=previous["survey"], 
                   convo_data=previous["convo_data"])
    
    @classmethod
    def build(cls, username: str, patient: Patient, start_time: str, chat_mode: str):
        return cls(username=username, patient=patient, start_time=start_time, chat_mode=chat_mode) 
            
    def add_feedback(self):
        self.feedback = Feedback.build(patient=self.patient, messages=self.messages, post_note_inputs=self.post_note_inputs)
    
    # def add_key_findings(self, findings: str):
    #     self.post_note_inputs["Key Findings"] = findings

    def add_other_inputs(self, post_note_inputs: dict):
        self.post_note_inputs = post_note_inputs
    
    def add_message(self, message: Message) -> None:
        if message.type and message.role and message.content:
            self.messages.append(message)
    
    def add_survey(self, survey: str) -> None:
        self.survey = survey
    
    def record_time(self, checkpoint: str) -> None:
        current_time = datetime.now().isoformat()
        self.times[current_time] = checkpoint

    def update_tokens(self, tokens: dict) -> None:
        self.tokens = tokens

    def finish(self) -> None:
        self.finished = True

    def store_convo_data(self) -> None:
        temp = {}
        temp["messages"] = st.session_state["messages"]
        temp["convo_memory"] = st.session_state["convo_memory"]
        temp["convo_summary"] = st.session_state["convo_summary"]
        self.convo_data = temp

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