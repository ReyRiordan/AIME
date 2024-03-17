from lookups import *
import json
from openai import OpenAI

from .patient import *
from .message import *
import web_methods

class Diagnosis:

    def __init__(self, patient: Patient, inputs: dict[str, str]):
        # Attributes
        self.weights = patient.grading["Diagnosis"]  # dict{str, dict{str, int}}
        self.classified = None                       # dict{str, dict{str, str}}
        self.checklists = None                       # dict{str, dict{str, bool}}
        self.score = None                            # int
        self.maxscore = None                         # int
        
        
        # Intialize the checklists
        self.checklists = {"Summary": {}, 
                           "Main": {}, 
                           "Secondary": {}}
        for label in self.weights["Summary"]:
            self.checklists["Summary"][label] = False
        for condition in self.weights["Main"]:
            self.checklists["Main"][condition] = False
        for condition in self.weights["Secondary"]:
            self.checklists["Secondary"][condition] = False
        
        # Grade the summary
        sum_prompt = GRADE_SUM_PROMPT
        for label in self.weights["Summary"]:
            sum_prompt += f"[{label}]\n{LABEL_DESCS[label]}\n"
        output = web_methods.generate_classifications(sum_prompt, inputs["Summary"])
        sum_labels = json.loads(output)["output"]
        for label in sum_labels:
            if label in self.checklists["Summary"]:
                self.checklists["Summary"][label] = True

        # Dict to see user input and corresponding matched conditions
        self.classified = {"Main": {}, 
                           "Secondary": {}}
        
        # Grade the conditions
        main_prompt = GRADE_DIAG_PROMPT
        valid_conditions = []
        for condition in self.checklists["Main"]:
            if condition not in valid_conditions:
                valid_conditions.append(condition)
        for condition in self.checklists["Secondary"]:
            if condition not in valid_conditions:
                valid_conditions.append(condition)
        main_prompt += json.dumps(valid_conditions)
        user_inputs = [inputs["Main"]] + [diagnosis for diagnosis in inputs["Secondary"]]
        print(f"User inputs: {user_inputs}\n")
        output = web_methods.generate_matches(main_prompt, json.dumps(user_inputs))
        matches = json.loads(output)["output"]
        print(f"Matches: {matches}\n")

        self.classified["Main"][inputs["Main"]] = matches[inputs["Main"]]
        if matches[inputs["Main"]] in self.checklists["Main"]:
            self.checklists["Main"][matches[inputs["Main"]]] = True
        for diagnosis in inputs["Secondary"]:
            self.classified["Secondary"][diagnosis] = matches[diagnosis]
            if matches[diagnosis] in self.checklists["Secondary"]:
                self.checklists["Secondary"][matches[diagnosis]] = True
        
        # Calculate scoring
        self.scores = {"Summary": 0,
                       "Main": 0,
                       "Secondary": 0}
        self.maxscores = {"Summary": 0,
                          "Main": 8,
                          "Secondary": 2}
        for label in self.checklists["Summary"]:
            if self.checklists["Summary"][label]:
                self.scores["Summary"] += self.weights["Summary"][label]
            self.maxscores["Summary"] += self.weights["Summary"][label]
        for condition in self.checklists["Main"]:
            if self.checklists["Main"][condition]:
                self.scores["Main"] += self.weights["Main"][condition]
        for condition in self.checklists["Secondary"]:
            if self.checklists["Secondary"][condition]:
                self.scores["Secondary"] += self.weights["Secondary"][condition]
    
    def get_dict(self):
        to_return = {"weights": self.weights, 
                     "classified": self.classified, 
                     "checklists": self.checklists, 
                     "scores": self.scores, 
                     "maxscores": self.maxscores}
        return to_return