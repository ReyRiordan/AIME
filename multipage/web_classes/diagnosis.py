from lookups import *
import json
from openai import OpenAI
import pydantic 
from typing import Optional, List


from .patient import *
from .message import *
import web_methods

class Diagnosis(pydantic.BaseModel):
    matches : Optional[dict]
    grades: Optional[dict]
    scores : Optional[dict]
    maxscores : Optional[dict] 


    # Attributes
        # matches = None                       # dict{str, dict{str, str}}
        # checklists = None                       # dict{str, dict{str, bool}}
        # score = None                            # dict{int}
        # maxscore = None                         # dict{int}
    
    @classmethod
    def build(cls, patient: Patient, inputs: dict[str, str]):
                
        # Intialize big grades dict (except rationale b/c need potential grading first to initialize)
        patient_grading = patient.grading["Diagnosis"]
        grades = {"Summary": {}, # label: {weight, score}
                  "Rationale": {}, # condition: {weight, score}
                  "Potential": {}, # condition: [{desc, sign, weight, score}, etc.]
                  "Final": {}} # condition: {weight, score}
        for label, weight in patient_grading["Summary"].items():
            grades["Summary"][label] = {"weight": weight, "score": False}
        for condition, weight in patient_grading["Potential"].items():
            grades["Potential"][condition] = {"weight": weight, "score": False}
        for condition, weight in patient_grading["Final"].items():
            grades["Final"][condition] = {"weight": weight, "score": False}
        
        # Initialize dict to see user input and corresponding matched conditions
        matches = {"Potential": {}, 
                   "Final": {}}
        
        # Grade the summary
        sum_prompt = GRADE_SUM_PROMPT
        for label in grades["Summary"]:
            sum_prompt += f"[{label}]\n{LABEL_DESCS[label]}\n"
        output = web_methods.generate_classifications(sum_prompt, inputs["Summary"])
        print(output + "\n\n")
        sum_labels = json.loads(output)
        for label in sum_labels:
            if label in grades["Summary"]:
                grades["Summary"][label]["score"] = True
        
        # Grade the potential and final conditions
        main_prompt = GRADE_DIAG_PROMPT
        valid_conditions = []
        for condition in grades["Potential"]:
            if condition not in valid_conditions:
                valid_conditions.append(condition)
        for condition in grades["Final"]:
            if condition not in valid_conditions:
                valid_conditions.append(condition)
        main_prompt += json.dumps(valid_conditions)
        user_inputs = [diagnosis for diagnosis in inputs["Potential"]] + [inputs["Final"]]
        # print(f"User inputs: {user_inputs}\n")
        output = web_methods.generate_matches(main_prompt, json.dumps(user_inputs))
        print(output + "\n\n") # debugging
        input_matches = json.loads(output)
        print(f"Matches: {input_matches}\n\n") # debugging
        for diagnosis in inputs["Potential"]:
            matches["Potential"][diagnosis] = input_matches[diagnosis]
            if input_matches[diagnosis] in grades["Potential"]:
                grades["Potential"][input_matches[diagnosis]]["score"] = True
        matches["Final"][inputs["Final"]] = input_matches[inputs["Final"]]
        if input_matches[inputs["Final"]] in grades["Final"]:
            grades["Final"][input_matches[inputs["Final"]]]["score"] = True
        
        # Initialize rationale grading based on what potential conditions user got right
        for condition in patient_grading["Rationale"]:
            if grades["Potential"][condition]["score"]:
                grades["Rationale"][condition] = []
                for reasoning in patient_grading["Rationale"][condition]:
                    to_append = reasoning.copy()
                    to_append["score"] = False
                    grades["Rationale"][condition].append(to_append)
        
        # Grade the rationale
        rat_prompt = GRADE_RAT_PROMPT
        for condition, reasonings in grades["Rationale"].items():
            reasonings_dict = {} # {id: "IMPLIES/REFUTES: desc"}
            id = 1
            for reasoning in reasonings:
                sign = "IMPLIES: " if reasoning["sign"] else "REFUTES: "
                reasonings_dict[id] = sign + reasoning["desc"]
                id += 1
            rat_prompt += f"\"{condition}\" {reasonings_dict}\n"
        print(rat_prompt + "\n\n") # debugging
        output = web_methods.generate_classifications(rat_prompt, inputs["Rationale"])
        print(output + "\n\n") # debugging
        rat_grades = json.loads(output) # {condition: [id, id, etc.]} (only ids that were present)
        for condition in rat_grades:
            for id in rat_grades[condition]:
                grades["Rationale"][condition][id-1]["score"] = True # prompted ids are 1 start but indices are 0 start
        
        # Calculate scoring
        scores = {"Summary": {"raw": 0, "max": 0},
                  "Rationale": {"raw": 0, "max": 0},
                  "Potential": {"raw": 0, "max": 3},
                  "Final": {"raw": 0, "max": 8}}
        for label in grades["Summary"]:
            weight = grades["Summary"][label]["weight"]
            if grades["Summary"][label]["score"]:
                scores["Summary"]["raw"] += weight
            scores["Summary"]["max"] += weight
        for condition in grades["Rationale"]:
            for id in checklists["Rationale"][condition]:
                if checklists["Rationale"][condition][id]:
                    scores["Rationale"] += grading["Rationale"][condition][id-1]["weight"] # list index starts at 0 but id starts at 1
                maxscores["Rationale"] += grading["Rationale"][condition][id-1]["weight"]
        for condition in checklists["Potential"]:
            if checklists["Potential"][condition]:
                scores["Potential"] += grading["Potential"][condition]
        for condition in checklists["Final"]:
            if checklists["Final"][condition]:
                scores["Final"] += grading["Final"][condition]

        return cls(matches=matches, grades=grades, scores=scores, maxscores=maxscores)

    # def get_dict(self):
    #     to_return = {"grading": self.grading, 
    #                  "classified": self.classified, 
    #                  "checklists": self.checklists, 
    #                  "scores": self.scores, 
    #                  "maxscores": self.maxscores}
    #     return to_return