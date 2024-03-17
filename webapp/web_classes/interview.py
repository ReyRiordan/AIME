from lookups import *
import json
from openai import OpenAI
import datetime as date

from .patient import *
from .message import *
from .feedback import *

class Interview:

    def __init__(self, username: str, patient: Patient):
        #Attributes
        self.__username = username      # str
        self.__patient = patient        # Patient
        self.__messages = []            # list[Message]
        self.__user_diagnosis = None     # dict{str, str/list[str]}
        self.__feedback = None          # Feedback
            
    def add_feedback(self):
        self.__feedback = Feedback(self.__patient, self.__messages, self.__user_diagnosis)
    
    def add_user_diagnosis(self, summary: str, main_diagnosis: str, main_rationale: str, secondary_diagnoses: list[str]):
        self.__user_diagnosis = {"Summary": summary, 
                                 "Main": main_diagnosis, 
                                 "Rationale": main_rationale, 
                                 "Secondary": secondary_diagnoses}
    
    def add_message(self, message: Message) -> None:
        if message.type and message.role and message.content:
            self.__messages.append(message)
    
    def get_username(self) -> str:
        return self.__username
    
    def get_patient(self) -> Patient:
        return self.__patient
    
    def get_messages(self) -> list[Message]:
        return self.__messages
    
    def get_user_diagnosis(self) -> dict[str, str]:
        return self.__user_diagnosis
    
    def get_feedback(self) -> Feedback:
        return self.__feedback

    def get_dict(self):
        currentDateTime=date.datetime.now()
        to_return = {"date_time": str(currentDateTime), 
                     "username": self.__username, 
                     "patient": self.__patient.get_dict(), 
                     "messages": [message.get_dict() for message in self.__messages], 
                     "user_diagnosis": self.__user_diagnosis if self.__user_diagnosis else None, 
                     "feedback": self.__feedback.get_dict() if self.__feedback else None}
        return to_return

    def get_json(self):
        return json.dumps(self.get_dict(),indent=4)