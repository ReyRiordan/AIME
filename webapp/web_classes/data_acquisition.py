from lookups import *
import json
from openai import OpenAI

from .patient import *
from .message import *
from .data_category import DataCategory
from web_methods.LLM import classifier

class DataAcquisition:

    def __init__(self, patient: Patient, messages: list[Message]):
        # Attributes
        self.datacategories = None  # list[DataCategory]
        self.weights = None         # dict{str, dict{str, int}}
        self.checklists = None      # dict{str, dict{str, bool}}
        self.scores = None          # dict{str, int}
        self.maxscores = None       # dict{str, int}

        # Only data categories for patient
        self.datacategories = []
        for category in patient.grading["DataAcquisition"]:
            self.datacategories.append(DataCategory(category, patient))
        self.weights = patient.grading["DataAcquisition"]

        # Label all messages according to categories
        for category in self.datacategories:
            classifier(LLM, category, messages)
        # Add annotations after classifying is done
        for message in messages:
            message.add_highlight()
            message.add_annotation()
        
        # Initialize all grades for each category to label: False
        self.checklists = {}
        for category in self.datacategories:
            self.checklists[category.name] = {label: False for label in self.weights[category.name]}

        # Iterate through messages and grade checklists
        for message in messages:
            for category in self.datacategories:
                if category.name in message.labels:
                    labels = message.labels[category.name]
                    for label in labels:
                        self.checklists[category.name][label] = True

        # Calculate scoring for each category
        self.scores = {}
        self.maxscores = {}
        for category in self.datacategories:
            self.scores[category.name] = self.get_score(category)
            self.maxscores[category.name] = self.get_maxscore(category)
        
    def get_score(self, category: DataCategory) -> int:
        # Get weights from patient and grades from self
        weights = self.weights[category.name]
        label_checklist = self.checklists[category.name]
        # Calculate score from weights and grades
        score = 0
        for label in weights:
            if label_checklist[label]: 
                score += weights[label]
        return score
    
    def get_maxscore(self, category: DataCategory) -> int:
        # Get weights from patient
        weights = self.weights[category.name]
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