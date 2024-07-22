from lookups import *
import json
from openai import OpenAI
import pydantic 
from typing import Optional, List


from .patient import *
from .message import *
import web_methods

class Diagnosis(pydantic.BaseModel):
    grades: Optional[dict]
    matches : Optional[dict]
    scores : Optional[dict]


    # Attributes
        # grades = None             # dict{str, dict{str, dict{?}}}
        # matches = None            # dict{str, dict{str, str}}
        # scores = None             # dict{str, dict{str, int}}
    
    @classmethod
    def build(cls, patient: Patient, inputs: dict[str, str]):
        
        # Intialize big grades dict (except rationale b/c need potential grading first to initialize)
        patient_grading = patient.grading["Diagnosis"]
        grades = {"Summary": {}, # label: {weight, score}
                  "Rationale": {"yes": {}, "no": {}}, # condition: [{desc, sign, weight, score}, etc.]
                  "Potential": {}, # condition: {weight, score}
                  "Final": {}} # condition: {weight, score}
        for label, weight in patient_grading["Summary"].items():
            grades["Summary"][label] = {"weight": weight, "score": False}
        for condition, weight in patient_grading["Potential"].items():
            grades["Potential"][condition] = {"weight": weight, "score": False}
        for condition, weight in patient_grading["Final"].items():
            grades["Final"][condition] = {"weight": weight, "score": False}
        
        # Initialize dict to see user input and corresponding matched conditions
        matches = {"Potential": {}, # input: match
                   "Final": {}} # input: match
        
        # Grade the summary
        sum_prompt = GRADE_SUM_PROMPT
        for label in grades["Summary"]:
            sum_prompt += f"[{label}]\n{patient.label_descs[label]}\n"
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
        for condition in patient_grading["Potential"]:
            boolean = "yes" if grades["Potential"][condition]["score"] else "no"
            grades["Rationale"][boolean][condition] = []
            for reasoning in patient_grading["Rationale"][condition]:
                to_append = reasoning.copy()
                if boolean == "yes":
                    to_append["score"] = False
                grades["Rationale"][boolean][condition].append(to_append)
        
        # Grade the rationale
        if grades["Rationale"]["yes"]:
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
        
        # Initialize scoring (except rationale, individual condition scores added after potential grading)
        scores = {"Summary": {"raw": 0, "max": 0},
                  "Rationale": {"total": {"raw": 0, "max": 0}},
                  "Potential": {"raw": 0, "max": 0},
                  "Final": {"raw": 0, "max": 0}}
        
        # Calculate scoring
        for label in grades["Summary"]:
            weight = grades["Summary"][label]["weight"]
            if grades["Summary"][label]["score"]:
                scores["Summary"]["raw"] += weight
            scores["Summary"]["max"] += weight
        for condition in grades["Rationale"]["yes"]: # for listed potentials
            scores["Rationale"][condition] = {"raw": 0, "max": 0}
            for reasoning in grades["Rationale"]["yes"][condition]:
                weight = reasoning["weight"]
                if reasoning["score"]:
                    scores["Rationale"][condition]["raw"] += weight
                    scores["Rationale"]["total"]["raw"] += weight
                scores["Rationale"][condition]["max"] += weight
                scores["Rationale"]["total"]["max"] += weight
        for condition in grades["Rationale"]["no"]: # for not listed potentials
            scores["Rationale"][condition] = {"max": 0}
            for reasoning in grades["Rationale"]["no"][condition]:
                scores["Rationale"][condition]["max"] += reasoning["weight"]
        for condition in grades["Potential"]:
            weight = grades["Potential"][condition]["weight"]
            if grades["Potential"][condition]["score"]:
                scores["Potential"]["raw"] += weight
            scores["Potential"]["max"] += weight
        for condition in grades["Final"]:
            weight = grades["Final"][condition]["weight"]
            if grades["Final"][condition]:
                scores["Final"]["raw"] += weight
            scores["Final"]["max"] += weight

        return cls(grades=grades, matches=matches, scores=scores)