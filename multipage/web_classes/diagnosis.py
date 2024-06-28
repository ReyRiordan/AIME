from lookups import *
import json
from openai import OpenAI
import pydantic 
from typing import Optional, List


from .patient import *
from .message import *
import web_methods

class Diagnosis(pydantic.BaseModel):
    grading: dict
    classified : Optional[dict]
    checklists: Optional[dict]
    scores : Optional[dict]
    maxscores : Optional[dict] 


    # Attributes
        # grading = patient.grading["Diagnosis"]  # dict{str, dict{str, int}}
        # classified = None                       # dict{str, dict{str, str}}
        # checklists = None                       # dict{str, dict{str, bool}}
        # score = None                            # dict{int}
        # maxscore = None                         # dict{int}
    
    @classmethod
    def build(cls, patient: Patient, inputs: dict[str, str]):
        grading = patient.grading["Diagnosis"]
                
        # Intialize the checklists other than rationale
        checklists = {"Summary": {}, 
                      "Rationale": {}, 
                      "Potential": {}, 
                      "Final": {}}
        for label in grading["Summary"]:
            checklists["Summary"][label] = False
        for condition in grading["Potential"]:
            checklists["Potential"][condition] = False
        for condition in grading["Final"]:
            checklists["Final"][condition] = False
        
        # Grade the summary
        sum_prompt = GRADE_SUM_PROMPT
        for label in grading["Summary"]:
            sum_prompt += f"[{label}]\n{LABEL_DESCS[label]}\n"
        output = web_methods.generate_classifications(sum_prompt, inputs["Summary"])
        print(output + "\n\n")
        sum_labels = json.loads(output)
        for label in sum_labels:
            if label in checklists["Summary"]:
                checklists["Summary"][label] = True

        # Dict to see user input and corresponding matched conditions
        classified = {"Potential": {}, 
                      "Final": {}}
        
        # Grade the conditions
        main_prompt = GRADE_DIAG_PROMPT
        valid_conditions = []
        for condition in checklists["Potential"]:
            if condition not in valid_conditions:
                valid_conditions.append(condition)
        for condition in checklists["Final"]:
            if condition not in valid_conditions:
                valid_conditions.append(condition)
        main_prompt += json.dumps(valid_conditions)
        user_inputs = [diagnosis for diagnosis in inputs["Potential"]] + [inputs["Final"]]
        # print(f"User inputs: {user_inputs}\n")
        output = web_methods.generate_matches(main_prompt, json.dumps(user_inputs))
        print(output + "\n\n")
        matches = json.loads(output)
        print(f"Matches: {matches}\n\n")

        for diagnosis in inputs["Potential"]:
            classified["Potential"][diagnosis] = matches[diagnosis]
            if matches[diagnosis] in checklists["Potential"]:
                checklists["Potential"][matches[diagnosis]] = True
        classified["Final"][inputs["Final"]] = matches[inputs["Final"]]
        if matches[inputs["Final"]] in checklists["Final"]:
            checklists["Final"][matches[inputs["Final"]]] = True

        # Initialize rationale checklist
        for condition in grading["Rationale"]:
            if checklists["Potential"][condition]:
                checklists["Rationale"][condition] = {} # {condition: {id: True/False}
                id = 1
                for reasoning in grading["Rationale"][condition]:
                    checklists["Rationale"][condition][id] = False
                    id += 1
        
        # Grade the rationale
        rat_prompt = GRADE_RAT_PROMPT
        for condition, reasonings in grading["Rationale"].items():
            reasonings_dict = {} # {id: "IMPLIES/REFUTES: desc"}
            id = 1
            for reasoning in reasonings:
                sign = "IMPLIES: " if reasoning["sign"] else "REFUTES: "
                reasonings_dict[id] = sign + reasoning["desc"]
                id += 1
            rat_prompt += f"\"{condition}\" {reasonings_dict}\n"
        print(rat_prompt + "\n\n")
        output = web_methods.generate_classifications(rat_prompt, inputs["Rationale"])
        print(output + "\n\n")
        rat_grades = json.loads(output) # {condition: [id, id, etc.]} (only ids that were present)
        for condition in rat_grades:
            for id in rat_grades[condition]:
                checklists["Rationale"][condition][id] = True

        # print(checklists)
        
        # Calculate scoring
        scores = {"Summary": 0,
                  "Rationale": 0,
                  "Potential": 0,
                  "Final": 0}
        maxscores = {"Summary": 0,
                     "Rationale": 0,
                     "Potential": 3,
                     "Final": 8}
        for label in checklists["Summary"]:
            if checklists["Summary"][label]:
                scores["Summary"] += grading["Summary"][label]
            maxscores["Summary"] += grading["Summary"][label]
        for condition in checklists["Rationale"]:
            for statement in checklists["Rationale"][condition]:
                if checklists["Rationale"][condition][statement]:
                    scores["Rationale"] += grading["Rationale"][condition][statement]
                maxscores["Rationale"] += grading["Rationale"][condition][statement]
        for condition in checklists["Potential"]:
            if checklists["Potential"][condition]:
                scores["Potential"] += grading["Potential"][condition]
        for condition in checklists["Final"]:
            if checklists["Final"][condition]:
                scores["Final"] += grading["Final"][condition]

        return cls(grading=grading, classified=classified, checklists=checklists, scores=scores, maxscores=maxscores)

    # def get_dict(self):
    #     to_return = {"grading": self.grading, 
    #                  "classified": self.classified, 
    #                  "checklists": self.checklists, 
    #                  "scores": self.scores, 
    #                  "maxscores": self.maxscores}
    #     return to_return