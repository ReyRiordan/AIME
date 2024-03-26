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

    datacategories: List[DataCategory]      # list[DataCategory]
    weights : Optional[List]                # dict{str, dict{str, int}}
    checklists : Optional[dict]             # dict{str, dict{str, bool}}
    scores :  Optional[dict]                 # dict{str, int}
    maxscores : Optional[dict]              # dict{str, int}
    
    def __init__(self, patient: Patient, messages: list[Message]):
        # Attributes
        # self.datacategories = None  # list[DataCategory]
        # self.weights = None         # dict{str, dict{str, int}}
        # self.checklists = None      # dict{str, dict{str, bool}}
        # self.scores = None          # dict{str, int}
        # self.maxscores = None       # dict{str, int}

        # Only data categories for patient
        datacategories= []
        for category in patient.grading["Data Acquisition"]:
            datacategories.append(DataCategory(name=category, patient=patient))
        weights = patient.grading["Data Acquisition"]


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
            for category in datacategories:
                classifier(category, batch)
            st.write(f"Batch {i+1} complete.")
        
        # Add annotations after classifying is done
        for message in messages:
            message.add_highlight()
            message.add_annotation()
        
        # Initialize all grades for each category to label: False
        checklists = {}
        for category in datacategories:
            checklists[category.name] = {label: False for label in weights[category.name]}

        # Iterate through messages and grade checklists
        for message in messages:
            for category in datacategories:
                if category.name in message.labels:
                    labels = message.labels[category.name]
                    for label in labels:
                        if label not in checklists[category.name]: # handle weird generated label name cases
                            raise ValueError(label + " is an unknown label.")
                        checklists[category.name][label] = True

        # Calculate scoring for each category
        scores = {}
        maxscores = {}
        for category in datacategories:
            scores[category.name] = self.get_score(weights,category)
            maxscores[category.name] = self.get_maxscore(weights,category)
        
        super().__init__(datacategories=datacategories,weights=weights,checklists=checklists,scores=scores,maxscores=maxscores)

    def get_score(self, weights, category: DataCategory) -> int:
        # Get weights from patient and grades from self
        # note: slight change to account for pydantic 
        
        weights = weights[category.name]
        label_checklist = self.checklists[category.name]
        # Calculate score from weights and grades
        score = 0
        for label in weights:
            if label_checklist[label]: 
                score += weights[label]
        return score
    
    def get_maxscore(self, weights, category: DataCategory) -> int:
        # Get weights from patient
        weights = weights[category.name]
        # Calculate max score from weights
        max = 0
        for label in weights:
            max += weights[label]
        return max
    
    def get_dict(self):
        to_return = {"datacategories": [category.get_dict() for category in self.datacategories], 
                     "weights": self.weights, 
                     "checklists": self.checklists, 
                     "scores": self.scores, 
                     "maxscores": self.maxscores}
        return to_return