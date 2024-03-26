from lookups import *
import json
from openai import OpenAI
import pydantic 
from typing import Optional, List

from .patient import *
from .message import *
from .data_acquisition import *
from .diagnosis import *
            
class Feedback(pydantic.BaseModel):

    data_acquisiton: Optional[DataAcquisition] = None   #DataAcquisition
    diagnosis: Optional[Diagnosis] = None               #Diagnosis

    def __init__(self, patient: Patient, messages: list[Message], user_diagnosis: dict[str, str]):
        # Attributes
        super().__init__(data_acquisition = DataAcquisition(patient=patient,messages=messages),diagnosis=Diagnosis(patient=patient,inputs=user_diagnosis))

        # self.data_acquisition = DataAcquisition(patient, messages)
        # self.diagnosis = Diagnosis(patient, user_diagnosis)
    
    def get_dict(self):
        to_return = {"Data Acquisition": self.data_acquisiton.get_dict(), 
                     "Diagnosis": self.diagnosis.get_dict()}
        return to_return