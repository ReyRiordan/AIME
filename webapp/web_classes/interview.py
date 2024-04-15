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
    date_time :str = str(date.datetime.now())       
    username :str                                   # str
    patient : Patient                               # Patient
    messages : Optional[List[Message]]    = []       # list[Message]
    user_diagnosis : Optional[dict]       = None     # dict{str, str/list[str]}
    feedback : Optional[Feedback]             = None    # Feedback
    
    @classmethod
    def build(cls, username: str, patient: Patient):
        #Attributes
        # messages = []            # list[Message]
        # user_diagnosis = None     # dict{str, str/list[str]}
        # feedback = None          # Feedback

        return cls(username=username,patient=patient) 
            
    def add_feedback(self):
        self.feedback = Feedback.build(patient=self.patient, messages=self.messages, user_diagnosis=self.user_diagnosis)

    def add_user_diagnosis(self, summary: str, main_diagnosis: str, main_rationale: str, secondary_diagnoses: list[str]):
        self.user_diagnosis = {"Summary": summary, 
                                 "Main": main_diagnosis, 
                                 "Rationale": main_rationale, 
                                 "Secondary": secondary_diagnoses}
    
    def add_message(self, message: Message) -> None:
        if message.type and message.role and message.content:
            self.messages.append(message)
    
    def get_username(self) -> str:
        return self.username
    
    def get_patient(self) -> Patient:
        return self.patient
    
    def get_messages(self) -> list[Message]:
        return self.messages
    
    def get_user_diagnosis(self) -> dict[str, str]:
        return self.user_diagnosis
    
    def get_feedback(self) -> Feedback:
        return self.feedback

    def get_dict(self):
        currentDateTime=date.datetime.now()
        to_return = {"date_time": str(currentDateTime), 
                     "username": self.username, 
                     "patient": self.patient.get_dict(), 
                     "messages": [message.get_dict() for message in self.messages], 
                     "user_diagnosis": self.user_diagnosis if self.user_diagnosis else None, 
                     "feedback": self.feedback.get_dict() if self.feedback else None}
        return to_return

    def get_json(self):
        return json.dumps(self.get_dict(),indent=4)