from lookups import *
import json
from openai import OpenAI

from .patient import *
from .message import *
import web_methods

class Diagnosis:

    def __init__(self, patient: Patient, userdiagnosis: dict[str, str]):
        # Attributes
        self.weights = patient.grading["Diagnosis"]  # dict{str, dict{str, int}}
        self.classified = None                       # dict{str, dict{str, str}}
        self.checklists = None                       # dict{str, dict{str, bool}}
        self.score = None                            # int
        self.maxscore = None                         # int

        # Dict to see user input and corresponding matched conditions
        self.classified = {"Main": {}, 
                           "Secondary": {}}
        
        # Intialize the checklists
        self.checklists = {"Main": {}, 
                           "Secondary": {}}
        for condition in self.weights["Main"]:
            self.checklists["Main"][condition] = False
        for condition in self.weights["Secondary"]:
            self.checklists["Secondary"][condition] = False
        
        # Grade the checklists
        main_prompt = DIAG_PROMPT
        valid_conditions = []
        for condition in self.checklists["Main"]:
            if condition not in valid_conditions:
                valid_conditions.append(condition)
        for condition in self.checklists["Secondary"]:
            if condition not in valid_conditions:
                valid_conditions.append(condition)
        main_prompt += json.dumps(valid_conditions)
        user_inputs = [userdiagnosis["main_diagnosis"]] + [diagnosis for diagnosis in userdiagnosis["secondary_diagnoses"]]
        print(f"User inputs: {user_inputs}\n")
        output = web_methods.generate_matches(main_prompt, json.dumps(user_inputs))
        matches = json.loads(output)["output"]
        print(f"Matches: {matches}\n")

        self.classified["Main"][userdiagnosis["main_diagnosis"]] = matches[userdiagnosis["main_diagnosis"]]
        if matches[userdiagnosis["main_diagnosis"]] in self.checklists["Main"]:
            self.checklists["Main"][matches[userdiagnosis["main_diagnosis"]]] = True
        for diagnosis in userdiagnosis["secondary_diagnoses"]:
            self.classified["Secondary"][diagnosis] = matches[diagnosis]
            if matches[diagnosis] in self.checklists["Secondary"]:
                self.checklists["Secondary"][matches[diagnosis]] = True
        
        # Calculate scoring
        self.score = 0
        self.maxscore = 10 # Just 10 static for now
        for condition in self.checklists["Main"]:
            if self.checklists["Main"][condition]:
                self.score += self.weights["Main"][condition]
        for condition in self.checklists["Secondary"]:
            if self.checklists["Secondary"][condition]:
                self.score += self.weights["Secondary"][condition]
    
    def get_dict(self):
        to_return = {"weights": self.weights, 
                     "classified": self.classified, 
                     "checklists": self.checklists, 
                     "score": self.score, 
                     "maxscore": self.maxscore}
        return to_return