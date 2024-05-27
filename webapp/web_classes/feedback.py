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

    data_acquisition: Optional[DataAcquisition] = None  #DataAcquisition
    diagnosis: Optional[Diagnosis]             = None  #Diagnosis

    @classmethod
    def build(cls, patient: Patient, messages: list[Message], diagnosis_inputs: dict[str, str]):
        # Attributes
        to_return_data_acquisition = DataAcquisition.build(patient=patient, messages=messages)
        return cls(data_acquisition=to_return_data_acquisition, diagnosis=Diagnosis.build(patient=patient, inputs=diagnosis_inputs))

        # self.data_acquisition = DataAcquisition(patient, messages)
        # self.diagnosis = Diagnosis(patient, user_diagnosis)
    

    
    # DEPRECATED get_dict() method

    # def get_dict(self):
    #     to_return = {"Data Acquisition": self.data_acquisition.get_dict(), 
    #                  "Diagnosis": self.diagnosis.get_dict()}
    #     return to_return