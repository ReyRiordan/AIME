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
        self.all_label_descs = None                         # dict{str, str}
        self.example = None                                 # str
        self.used_label_descs = None                        # dict{str, str}
        self.class_prompt = None                            # str

        # Create classification prompt (patient dependent)
        class_base = CLASS_INPUT if self.type == "input" else CLASS_OUTPUT
        with open(class_base, "r", encoding="utf8") as class_base_file:
            base_raw = class_base_file.read()
            base_split = base_raw.split("|PATIENT DEPENDENT|")
            if len(base_split) != 3:
                raise ValueError("Base classification prompt should have 3 parts.")

        with open(DATACATEGORIES[name]["desc"], "r") as desc_json:
            full_desc = json.load(desc_json)
        self.all_label_descs = full_desc["labels"]
        self.example = full_desc["example"]

        self.used_label_descs = {}
        for label in patient.grading["DataAcquisition"][name]:
            self.used_label_descs[label] = self.all_label_descs[label]
        
        self.class_prompt = base_split[0]
        for label in self.used_label_descs:
            self.class_prompt += "[" + label.replace(" ", "_") + "] " + self.used_label_descs[label] + "\n"
        self.class_prompt += base_split[1] + self.example + base_split[2]
    
    def get_dict(self):
        to_return = {"name": self.name, 
                     "type": self.type, 
                     "header": self.header, 
                     "color": self.color, 
                     "highlight": self.highlight}
        return to_return