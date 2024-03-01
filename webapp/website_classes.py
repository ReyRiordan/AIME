from lookups import *
import json
from openai import OpenAI
import datetime as date

#TODO Make data for rest of classes "private" + getters and setters?

#TODO Move each class to its own separate file for cleanliness' sake. I'm lazy, u got it Rey

class Patient:

    def __init__(self, name):
        # Attributes
        self.name = name      # str
        self.case             # dict{str, list[dict{str, str/bool}]}
        self.grading          # dict{str, dict{str, dict{str, int}}}
        self.physical         # str path
        self.ECG              # str path
        self.convo_prompt     # str

        # Create virtual patient prompt
        with open(PATIENTS[name]["base"], "r", encoding="utf8") as base_prompt:
            base = base_prompt.read()
            base = base.replace("{patient}", name)
        self.convo_prompt = str(base)
        with open(PATIENTS[name]["case"], "r") as case_json:
            self.case = json.load(case_json)
        self.convo_prompt += self.process_case(self.case)

        # Assign physical and ECG data paths for patient for website display use
        self.physical = PATIENTS[name]["physical"]
        self.ECG = PATIENTS[name]["ECG"]

        # Extract grading for patient
        with open(PATIENTS[name]["grading"], "r") as grading_json:
            self.grading = json.load(grading_json)

    def process_case(self, case: dict[str, list[dict[str]]]) -> str:
        case_prompt = ""
        for category in case: 
            case_prompt += "[" + category + "] \n"
            if category == "Personal Details":
                for element in case[category]:
                    case_prompt += element["detail"] + ": " + element["line"] + " \n"
            elif category == "Chief Concern":
                case_prompt += case[category] + " \n"
            elif category == "History of Present Illness":
                for element in case[category]:
                    line = element["dim"] + ": " + element["line"]
                    if element["lock"]:
                        line = "<LOCKED> " + line
                    case_prompt += line + "\n"
            else:
                for element in case[category]:
                    line = element["line"]
                    if element["lock"]:
                        line = "<LOCKED> " + line
                    case_prompt += line + " \n"
        return case_prompt

    def get_dict(self):
        to_return = {"name": self.name, 
                     "case": self.case, 
                     "grading": self.grading, 
                     "physical": self.physical, 
                     "ECG": self.ECG}
        return to_return


class DataCategory:

    def __init__(self, name: str, patient: Patient):
        # Attributes
        self.name = name                                    # str
        self.type = DATACATEGORIES[name]["type"]            # str
        self.header = DATACATEGORIES[name]["header"]        # str
        self.color = DATACATEGORIES[name]["color"]          # str
        self.highlight = DATACATEGORIES[name]["highlight"]  # str
        self.all_label_descs                                # dict{str, str}
        self.example                                        # str
        self.used_label_descs                               # dict{str, str}
        self.class_prompt                                   # str

        # Create classification prompt (patient dependent)
        class_base = CLASS_INPUT if self.type == "input" else CLASS_OUTPUT
        with open(class_base, "r", encoding="utf8") as class_base_file:
            base_raw = class_base_file.read()
            base_split = base_raw.split("|PATIENT DEPENDENT|")
            if len(base_split) != 3:
                raise ValueError("Base classification prompt should have 3 parts.")

        with open(DATACATEGORIES[name]["desc"], "r") as desc_json:
            full_desc = json.load(desc_json)
        self.all_label_descs = full_desc["labels"]
        self.example = full_desc["example"]

        self.used_label_descs = {}
        for label in patient.grading["DataAcquisition"][name]:
            self.used_label_descs[label] = self.all_label_descs[label]
        
        self.class_prompt = base_split[0]
        for label in self.used_label_descs:
            self.class_prompt += "[" + label.replace(" ", "_") + "] " + self.used_label_descs[label] + "\n"
        self.class_prompt += base_split[1] + self.example + base_split[2]
    
    def get_dict(self):
        to_return = {"name": self.name, 
                     "type": self.type, 
                     "header": self.header, 
                     "color": self.color, 
                     "highlight": self.highlight}
        return to_return

class Message:
    #TODO Just a thought, perhaps arranging these all into one big dict? See get_dict
    def __init__(self, type: str, role: str, content: str):
        # Attributes
        self.type = type        # str
        self.role = role        # str  
        self.content = content  # str
        self.labels = {}        # dict{str, list[str]}
        self.annotation         # str
        self.highlight          # str

    def add_highlight(self):
        if self.labels:
            first_datacategory = next(iter(self.labels.keys())) # Access first key in dict
            self.highlight = DATACATEGORIES[first_datacategory]["highlight"]

    def add_annotation(self):
        all_labels = []
        for category in self.labels:
            all_labels.extend(self.labels[category])
        all_labels = list(dict.fromkeys(all_labels)) # Remove duplicates
        if all_labels: self.annotation = ", ".join(all_labels)
    
    def get_content(self):
        return self.content
    
    def get_dict(self): 
        to_return = {"type": self.type, 
                     "role": self.role, 
                     "content": self.content, 
                     "labels": self.labels, 
                     "annotation": self.annotation, 
                     "highlight": self.highlight}
        return to_return


class DataAcquisition:

    def __init__(self, patient: Patient, messages: list[Message]):
        # Attributes
        self.datacategories  # list[DataCategory]
        self.weights     # dict{str, dict{str, int}}
        self.checklists  # dict{str, dict{str, bool}}
        self.scores      # dict{str, int}
        self.maxscores   # dict{str, int}

        # Only data categories for patient
        self.datacategories = []
        for category in patient.grading["DataAcquisition"]:
            self.datacategories.append(DataCategory(category, patient))
        self.weights = patient.grading["DataAcquisition"]
        
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


class Diagnosis:

    def __init__(self, patient: Patient, userdiagnosis: dict[str, str]):
        # Attributes
        self.weights = patient.grading["Diagnosis"]  # dict{str, dict{str, int}}
        self.checklists                              # dict{str, dict{str, bool}}
        self.score                                   # int
        self.maxscore                                # int

        # Intialize the checklists
        self.checklists = {"Main": {}, 
                           "Secondary": {}}
        for condition in self.weights["Main"]:
            self.checklists["Main"][condition] = False
        for condition in self.weights["Secondary"]:
            self.checklists["Secondary"][condition] = False
        
        # Grade the checklists
        client = OpenAI()
        main_prompt = DIAG_PROMPT
        for condition in self.checklists["Main"]:
            main_prompt += condition + "\n"
        raw_output = client.chat.completions.create(model = DIAG_MODEL, 
                                                    temperature = DIAG_TEMP, 
                                                    messages = [{"role": "system", "content": main_prompt}, 
                                                                {"role": "user", "content": userdiagnosis["main_diagnosis"]}])
        matched_condition = raw_output.choices[0].message.content
        if matched_condition in self.checklists["Main"]:
            self.checklists["Main"][matched_condition] = True
        secondary_prompt = DIAG_PROMPT
        for condition in self.checklists["Secondary"]:
            secondary_prompt += condition + "\n"
        for diagnosis in userdiagnosis["secondary_diagnoses"]:
            raw_output = client.chat.completions.create(model = DIAG_MODEL, 
                                                        temperature = DIAG_TEMP, 
                                                        messages = [{"role": "system", "content": secondary_prompt}, 
                                                                    {"role": "user", "content": diagnosis}])
            matched_condition = raw_output.choices[0].message.content
            if matched_condition in self.checklists["Secondary"]:
                self.checklists["Secondary"][matched_condition] = True
        
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
                     "checklists": self.checklists, 
                     "score": self.score, 
                     "maxscore": self.maxscore}
        return to_return

            
class Feedback:

    def __init__(self, patient: Patient, messages: list[Message], userdiagnosis: dict[str, str]):
        # Attributes
        self.DataAcquisition = DataAcquisition(patient, messages)
        self.Diagnosis = Diagnosis(patient, userdiagnosis)
    
    def get_dict(self):
        to_return = {"DataAcquisition": self.DataAcquisition.get_dict(), 
                     "Diagnosis": self.Diagnosis.get_dict()}
        return to_return


class Interview:

    def __init__(self, username: str, patient: Patient):
        #Attributes
        self.__username = username                              # str
        self.__patient = patient                                # Patient
        self.__messages = []                                    # list[Message]
        self.__userdiagnosis = {"main_diagnosis": None,         # dict{str, str}
                                "main_rationale": None, 
                                "secondary_diagnosis": None}
        self.__feedback                                         # Feedback
            
    def add_feedback(self):
        self.__feedback = Feedback(self.__patient, self.__messages, self.__userdiagnosis)
    
    def add_userdiagnosis(self, main_diagnosis: str, main_rationale: str, secondary_diagnosis: str):
        self.__userdiagnosis["main_diagnosis"] = main_diagnosis
        self.__userdiagnosis["main_rationale"] = main_rationale
        self.__userdiagnosis["secondary_diagnosis"] = secondary_diagnosis
    
    def add_message(self, message: Message) -> None:
        if message.type and message.role and message.content:
            self.__messages.append(message)
    
    def get_username(self) -> str:
        return self.__username
    
    def get_patient(self) -> Patient:
        return self.__patient
    
    def get_messages(self) -> list[Message]:
        return self.__messages
    
    def get_userdiagnosis(self) -> dict[str, str]:
        return self.__userdiagnosis
    
    def get_feedback(self) -> Feedback:
        return self.__feedback

    def get_dict(self):
        currentDateTime=date.datetime.now()
        to_return = {"date_time": str(currentDateTime), 
                     "username": self.__username, 
                     "patient": self.__patient.get_dict(), 
                     "messages": [message.get_dict() for message in self.__messages], 
                     "userdiagnosis": self.__userdiagnosis, 
                     "feedback": self.__feedback.get_dict()}
        return to_return

    def get_json(self):
        return json.dumps(self.get_dict(),indent=4)
