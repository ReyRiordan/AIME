from lookups import *
import json
from openai import OpenAI
import pydantic 
from typing import Optional, List


from .patient import *
from .message import *
import web_methods

class Diagnosis(pydantic.BaseModel):
    weights: dict
    classified : Optional[dict]
    checklists: Optional[dict]
    scores : Optional[dict]
    maxscores : Optional[dict] 


    # Attributes
        # weights = patient.grading["Diagnosis"]  # dict{str, dict{str, int}}
        # classified = None                       # dict{str, dict{str, str}}
        # checklists = None                       # dict{str, dict{str, bool}}
        # score = None                            # dict{int}
        # maxscore = None                         # dict{int}
    
    @classmethod
    def build(cls, patient: Patient, inputs: dict[str, str]):
        weights = patient.grading["Diagnosis"]
                
        # Intialize the checklists
        checklists = {"Summary": {}, 
                      "Rationale": {}, 
                      "Main": {}, 
                      "Secondary": {}}
        for label in weights["Summary"]:
            checklists["Summary"][label] = False
        for statement in weights["Rationale"]:
            checklists["Rationale"][statement] = False
        for condition in weights["Main"]:
            checklists["Main"][condition] = False
        for condition in weights["Secondary"]:
            checklists["Secondary"][condition] = False
        
        # Grade the summary
        sum_prompt = GRADE_SUM_PROMPT
        for label in weights["Summary"]:
            sum_prompt += f"[{label}]\n{LABEL_DESCS[label]}\n"
        output = web_methods.generate_classifications(sum_prompt, inputs["Summary"])
        print(output + "\n\n")
        sum_labels = json.loads(output)
        for label in sum_labels:
            if label in checklists["Summary"]:
                checklists["Summary"][label] = True

        # Grade the rationale
        rat_prompt = GRADE_RAT_PROMPT
        id = 0
        for statement in weights["Rationale"]:
            rat_prompt += f"{id} {statement}\n"
            id += 1
        print(rat_prompt + "\n\n")
        output = web_methods.generate_classifications(rat_prompt, inputs["Rationale"])
        print(output + "\n\n")
        rat_ids = json.loads(output)
        statements_list = list(weights["Rationale"].keys())
        for id in rat_ids:
            statement = statements_list[id]
            if statement in checklists["Rationale"]:
                checklists["Rationale"][statement] = True

        # Dict to see user input and corresponding matched conditions
        classified = {"Main": {}, 
                      "Secondary": {}}
        
        # Grade the conditions
        main_prompt = GRADE_DIAG_PROMPT
        valid_conditions = []
        for condition in checklists["Main"]:
            if condition not in valid_conditions:
                valid_conditions.append(condition)
        for condition in checklists["Secondary"]:
            if condition not in valid_conditions:
                valid_conditions.append(condition)
        main_prompt += json.dumps(valid_conditions)
        user_inputs = [inputs["Main"]] + [diagnosis for diagnosis in inputs["Secondary"]]
        print(f"User inputs: {user_inputs}\n")
        output = web_methods.generate_matches(main_prompt, json.dumps(user_inputs))
        print(output + "\n\n")
        matches = json.loads(output)["output"]
        print(f"Matches: {matches}\n")

        classified["Main"][inputs["Main"]] = matches[inputs["Main"]]
        if matches[inputs["Main"]] in checklists["Main"]:
            checklists["Main"][matches[inputs["Main"]]] = True
        for diagnosis in inputs["Secondary"]:
            classified["Secondary"][diagnosis] = matches[diagnosis]
            if matches[diagnosis] in checklists["Secondary"]:
                checklists["Secondary"][matches[diagnosis]] = True

        # print(checklists)
        
        # Calculate scoring
        scores = {"Summary": 0,
                  "Rationale": 0,
                  "Main": 0,
                  "Secondary": 0}
        maxscores = {"Summary": 0,
                     "Rationale": 0,
                    "Main": 8,
                    "Secondary": 2}
        for label in checklists["Summary"]:
            if checklists["Summary"][label]:
                scores["Summary"] += weights["Summary"][label]
            maxscores["Summary"] += weights["Summary"][label]
        for statement in checklists["Rationale"]:
            if checklists["Rationale"][statement]:
                scores["Rationale"] += weights["Rationale"][statement]
            maxscores["Rationale"] += weights["Rationale"][statement]
        for condition in checklists["Main"]:
            if checklists["Main"][condition]:
                scores["Main"] += weights["Main"][condition]
        for condition in checklists["Secondary"]:
            if checklists["Secondary"][condition]:
                scores["Secondary"] += weights["Secondary"][condition]

        return cls(weights=weights,classified=classified,checklists=checklists,scores=scores,maxscores=maxscores)

    def get_dict(self):
        to_return = {"weights": self.weights, 
                     "classified": self.classified, 
                     "checklists": self.checklists, 
                     "scores": self.scores, 
                     "maxscores": self.maxscores}
        return to_return