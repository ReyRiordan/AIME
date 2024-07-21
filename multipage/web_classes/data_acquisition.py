from lookups import *
import json
from openai import OpenAI
import streamlit as st
import time
import pydantic
from typing import Optional, List

from .patient import *
from .message import *
from .data_category import DataCategory
from web_methods.LLM import classifier

class DataAcquisition(pydantic.BaseModel):

    data_categories: List[DataCategory]      # list[DataCategory]
    grades : Optional[dict]                 # dict{str, dict{str, dict{?}}}
    scores :  Optional[dict]                # dict{str, dict{str, int}}
    
    @classmethod
    def build(cls, patient: Patient, messages: list[Message]):
        # Attributes
        # self.datacategories = None    # list[DataCategory]
        # self.grades = None            # dict{str, dict{str, dict{?}}}
        # self.scores = None            # dict{str, dict{str, int}}

        # Only data categories for patient
        data_categories = []
        for category in patient.grading["Data Acquisition"]:
            data_categories.append(DataCategory.build(name=category, patient=patient))

        # Extract weights for easier access
        weights = patient.grading["Data Acquisition"]

        # Initialize all grades for each category to label: False
        grades = {category.name: {} for category in data_categories} # category: {label: {weight, score}}
        for category in data_categories:
            for label, weight in weights[category.name].items():
                grades[category.name][label] = {"weight": weight, "score": False}


        # Split messages into batches if needed
        if len(messages) > BATCH_MAX:
            num_batches = -(-len(messages) // BATCH_MAX) # Round up int division
            batch_size = -(-len(messages) // num_batches)
            batches = [messages[i*batch_size : (i+1)*batch_size] for i in range(num_batches)]
        else:
            batches = [messages]

        # 1 min estimated wait per batch
        st.write(f"{len(messages)} messages split into {len(batches)} batches, estimated wait time: {len(batches)} minutes.")

        # Label all messages according to categories
        for i, batch in enumerate(batches):
            if i > 0: time.sleep(BATCH_DELAY)
            for category in data_categories:
                classifier(category, batch)
            st.write(f"Batch {i+1} complete.")
        
        # Add annotations after classifying is done
        for message in messages:
            message.add_highlight()
            message.add_annotation()

        # Iterate through messages and grade checklists
        for message in messages:
            for category in data_categories:
                if category.name in message.labels:
                    labels = message.labels[category.name]
                    for label in labels:
                        if label not in grades[category.name]: # handle weird generated label name cases
                            raise ValueError(label + " is an unknown label.")
                        grades[category.name][label]["score"] = True

        # Calculate scores
        scores = {}
        for category in data_categories:
            scores[category.name] = {"raw": 0, "max": 0}
            for label, grade in grades[category.name].items():
                weight = grade["weight"]
                if grade["score"]:
                    scores[category.name]["raw"] += weight
                scores[category.name]["max"] += weight

        return cls(data_categories=data_categories,
                   grades=grades,
                   scores=scores)
    
    # def get_dict(self):
    #     to_return = {"datacategories": [category.get_dict() for category in self.datacategories], 
    #                  "weights": self.weights, 
    #                  "checklists": self.checklists, 
    #                  "scores": self.scores, 
    #                  "maxscores": self.maxscores}
    #     return to_return