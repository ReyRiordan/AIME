from lookups import *
import pydantic
from typing import Optional,List

class Message(pydantic.BaseModel):

    type: str
    role : str
    content : str
    labels: Optional[dict] = {}
    annotation: Optional[str] = None
    highlight: Optional[str] = None

    def add_highlight(self):
        DATACATEGORIES = {
            "General":      {"type": "input", 
                             "header": "General Questions", 
                             "color": "blue", 
                             "highlight": "#bae1ff"}, # light blue
            "Dimensions":   {"type": "output", 
                             "header": "Dimensions of Chief Concern", 
                             "color": "red", 
                             "highlight": "#ffb3ba"}, # light red
            "Associated":   {"type": "input", 
                             "header": "Associated Symptoms Questions", 
                             "color": "orange", 
                             "highlight": "#ffdfba"}, # light orange
            "Risk":         {"type": "input", 
                             "header": "Risk Factor Questions", 
                             "color": "violet", 
                             "highlight": "#f1cbff"}, # light violet
        }

        if self.labels:
            first_datacategory = next(iter(self.labels.keys())) # Access first key in dict
            self.highlight = DATACATEGORIES[first_datacategory]["highlight"]

    def add_annotation(self):
        all_labels = []
        for category in self.labels:
            all_labels.extend(self.labels[category])
        all_labels = list(dict.fromkeys(all_labels)) # Remove duplicates
        if all_labels: self.annotation = ", ".join(all_labels)
    
    
    # def get_dict(self): 
    #     to_return = {"type": self.type, 
    #                  "role": self.role, 
    #                  "content": self.content, 
    #                  "labels": self.labels, 
    #                  "annotation": self.annotation, 
    #                  "highlight": self.highlight}
    #     return to_return