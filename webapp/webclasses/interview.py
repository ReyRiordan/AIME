from lookups import *
import json
from openai import OpenAI
import datetime as date
from patient import *
from message import *
from data_acquisition import *
from diagnosis import *
from feedback import *

class Interview:

    def __init__(self, username: str, patient: Patient):
        #Attributes
        self.__username = username                              # str
        self.__patient = patient                                # Patient
        self.__messages = []                                    # list[Message]
        self.__userdiagnosis = {"main_diagnosis": None,         # dict{str, str}
                                "main_rationale": None, 
                                "secondary_diagnosis": None}
        self.__feedback                                         # Feedback
            
    def add_feedback(self):
        self.__feedback = Feedback(self.__patient, self.__messages, self.__userdiagnosis)
    
    def add_userdiagnosis(self, main_diagnosis: str, main_rationale: str, secondary_diagnosis: str):
        self.__userdiagnosis["main_diagnosis"] = main_diagnosis
        self.__userdiagnosis["main_rationale"] = main_rationale
        self.__userdiagnosis["secondary_diagnosis"] = secondary_diagnosis
    
    def add_message(self, message: Message) -> None:
        if message.type and message.role and message.content:
            self.__messages.append(message)
    
    def get_username(self) -> str:
        return self.__username
    
    def get_patient(self) -> Patient:
        return self.__patient
    
    def get_messages(self) -> list[Message]:
        return self.__messages
    
    def get_userdiagnosis(self) -> dict[str, str]:
        return self.__userdiagnosis
    
    def get_feedback(self) -> Feedback:
        return self.__feedback

    def get_dict(self):
        currentDateTime=date.datetime.now()
        to_return = {"date_time": str(currentDateTime), 
                     "username": self.__username, 
                     "patient": self.__patient.get_dict(), 
                     "messages": [message.get_dict() for message in self.__messages], 
                     "userdiagnosis": self.__userdiagnosis, 
                     "feedback": self.__feedback.get_dict()}
        return to_return

    def get_json(self):
        return json.dumps(self.get_dict(),indent=4)