from lookups import *
import json
from openai import OpenAI

from .patient import *
from .message import *
from .data_acquisition import *
from .diagnosis import *
            
class Feedback:

    def __init__(self, patient: Patient, messages: list[Message], userdiagnosis: dict[str, str]):
        # Attributes
        self.DataAcquisition = DataAcquisition(patient, messages)
        self.Diagnosis = Diagnosis(patient, userdiagnosis)
    
    def get_dict(self):
        to_return = {"Data Acquisition": self.DataAcquisition.get_dict(), 
                     "Diagnosis": self.Diagnosis.get_dict()}
        return to_return