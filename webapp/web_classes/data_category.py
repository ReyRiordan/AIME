from lookups import *
import json
from openai import OpenAI

from .patient import Patient

class DataCategory:

    def __init__(self, name: str, patient: Patient):
        # Attributes
        self.name = name                                    # str
        self.type = DATACATEGORIES[name]["type"]            # str
        self.header = DATACATEGORIES[name]["header"]        # str
        self.color = DATACATEGORIES[name]["color"]          # str
        self.highlight = DATACATEGORIES[name]["highlight"]  # str
        # self.example = None                                 # str
        self.class_prompt = None                            # str

        # Create classification prompt (patient dependent)
        class_base = CLASS_INPUT if self.type == "input" else CLASS_OUTPUT
        with open(class_base, "r", encoding="utf8") as class_base_file:
            base_raw = class_base_file.read()
            base_split = base_raw.split("|PATIENT DEPENDENT|")
            if len(base_split) != 2:
                raise ValueError("Base classification prompt should have 2 parts.")

        # self.example = LABEL_EXAMPLES[name]
        
        self.class_prompt = base_split[0]
        for label in patient.grading["Data Acquisition"][name]:
            self.class_prompt += "[" + label + "] " + LABEL_DESCS[label] + "\n"
        self.class_prompt += base_split[1]
        
        print(f"\n\n{self.class_prompt}\n\n") # debugging
    
    def get_dict(self):
        to_return = {"name": self.name, 
                     "type": self.type, 
                     "header": self.header, 
                     "color": self.color, 
                     "highlight": self.highlight}
        return to_return