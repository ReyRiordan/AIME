from lookups import *
import json
from openai import OpenAI
import datetime as date

#TODO Make data for rest of classes "private" + getters and setters?

#TODO Move each class to its own separate file for cleanliness' sake. I'm lazy, u got it Rey

class Patient:

    def __init__(self, name):
        # Assign name of patient
        self.name = name

        # Create virtual patient prompt
        with open(PATIENTS[name]["base"], "r", encoding="utf8") as base_prompt:
            base = base_prompt.read()
            base = base.replace("{patient}", name)
        self.convo_prompt = str(base)
        with open(PATIENTS[name]["case"], "r") as case_json:
            case = json.load(case_json)
        self.HPI = case["History of Present Illness"]
        self.convo_prompt += self.process_case(case)

        # Assign physical and ECG data paths for patient for website display use
        self.physical = PATIENTS[name]["physical"]
        self.ECG = PATIENTS[name]["ECG"]

        # Extract grading for patient
        with open(PATIENTS[name]["grading"], "r") as grading_json:
            self.grading = json.load(grading_json)
            self.weights_data = self.grading["data"]
            self.weights_diagnosis = self.grading["diagnosis"]

        

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
        patient_dict={}
        patient_dict["name"]=self.name
        patient_dict["weights"]=self.weights_data
        return patient_dict


class Category:

    def __init__(self, name: str, patient: Patient):
        # Initialize all the basic stuff using corresponding lookup dict
        self.name = name
        self.tab = CATEGORIES[name]["tab"]
        self.type = CATEGORIES[name]["type"]
        self.header = CATEGORIES[name]["header"]
        self.color = CATEGORIES[name]["color"]
        self.highlight = CATEGORIES[name]["highlight"]

        # Create classification prompt (patient dependent)
        class_base = CLASS_INPUT if self.type == "input" else CLASS_OUTPUT
        with open(class_base, "r", encoding="utf8") as class_base_file:
            base_raw = class_base_file.read()
            base_split = base_raw.split("|PATIENT DEPENDENT")
            if len(base_split) != 3:
                raise ValueError("Base classification prompt should have 3 parts.")

        with open(CATEGORIES[name]["desc"], "r") as desc_json:
            full_desc = json.load(desc_json)
        self.all_label_descs = full_desc["labels"] # dict[str, str]
        self.example = full_desc["example"] # str

        self.used_label_descs = {} # dict[str, str]
        for label in patient.weights_data[name]:
            self.used_label_descs[label] = self.all_label_descs[label]
        
        self.class_prompt = base_split[0]
        for label in self.used_label_descs:
            self.class_prompt += "[" + label.replace(" ", "_") + "] " + self.used_label_descs[label] + "\n"
        self.class_prompt += base_split[1] + self.example + base_split[2]
        

class Message:
    #TODO Just a thought, perhaps arranging these all into one big dict? See get_dict
    def __init__(self, type: str, role: str, content: str):
        self.type = type #str
        self.role = role #str  
        self.content = content #str
        self.labels = {} # dict[str, list[str]]
        self.highlight = None
        self.annotation = None

    def add_highlight(self):
        if self.labels:
            first_category = next(iter(self.labels.keys())) # Access first key in dict
            self.highlight = CATEGORIES[first_category]["highlight"]

    def add_annotation(self):
        all_labels = []
        for category in self.labels:
            all_labels.extend(self.labels[category])
        all_labels = list(dict.fromkeys(all_labels)) # Remove duplicates
        if all_labels: self.annotation = ", ".join(all_labels)
    
    def get_content(self):
        return self.content
    
    def get_dict(self): 
        message_dict={}
        message_dict["type"] = self.type
        message_dict["role"] = self.role
        message_dict["content"]=self.content
        message_dict["labels"]=self.labels
        return message_dict


class DataGrades:

    def __init__(self, patient: Patient, categories: list[Category], messages: list[Message]):
        self.patient = patient
        self.categories = categories
        self.weights = patient.weights_data
        
        # Initialize all grades for each category to label: False
        self.label_checklist = {} # dict[str, dict[str, bool]]
        for category in categories:
            self.label_checklist[category.name] = {label: False for label in self.weights[category.name]}

        # Iterate through messages and grade checklist
        for message in messages:
            for category in categories:
                if category.name in message.labels:
                    labels = message.labels[category.name]
                    for label in labels:
                        self.label_checklist[category.name][label] = True

        # Calculate scoring for each category
        self.scores = {}
        self.max_scores = {}
        for category in categories:
            self.scores[category.name] = self.get_score(category)
            self.max_scores[category.name] = self.get_maxscore(category)
        
    def get_score(self, category: Category) -> int:
        # Get weights from patient and grades from self
        weights = self.weights[category.name]
        label_checklist = self.label_checklist[category.name]

        # Calculate score from weights and grades
        score = 0
        for label in weights:
            if label_checklist[label]: 
                score += weights[label]
        
        return score
    
    def get_maxscore(self, category: Category) -> int:
        # Get weights from patient
        weights = self.weights[category.name]

        # Calculate max score from weights
        max = 0
        for label in weights:
            max += weights[label]
        
        return max
    
    def get_dict(self):
        to_return={}
        to_return["scores"]=self.scores
        to_return["max_scores"]=self.max_scores
        to_return["label_checklist"]=self.label_checklist
        return to_return



class Diagnosis:

    def __init__(self, main_diagnosis: str, main_rationale: str, secondary_diagnoses: list[str]):
        self.main_diagnosis = main_diagnosis
        self.main_rationale = main_rationale
        self.secondary_diagnoses = secondary_diagnoses


class DiagnosisGrades:

    def __init__(self, patient: Patient, diagnosis: Diagnosis):
        self.patient = patient
        self.diagnosis = diagnosis
        self.weights = patient.weights_diagnosis

        # Intialize the checklist
        self.main_checklist = {}
        for condition in self.weights["Main"]:
            self.main_checklist[condition] = False
        self.secondary_checklist = {}
        for condition in self.weights["Secondary"]:
            self.secondary_checklist[condition] = False
        
        # Grade the checklists
        client = OpenAI()
        main_prompt = DIAG_PROMPT
        for condition in self.main_checklist:
            main_prompt += condition + "\n"
        raw_output = client.chat.completions.create(model = DIAG_MODEL, 
                                                    temperature = DIAG_TEMP, 
                                                    messages = [{"role": "system", "content": main_prompt}, 
                                                                {"role": "user", "content": diagnosis.main_diagnosis}])
        matched_condition = raw_output.choices[0].message.content
        print(diagnosis.main_diagnosis + ": " + matched_condition)
        if matched_condition in self.main_checklist:
            self.main_checklist[matched_condition] = True
        secondary_prompt = DIAG_PROMPT
        for condition in self.secondary_checklist:
            secondary_prompt += condition + "\n"
        for diagnosis in diagnosis.secondary_diagnoses:
            raw_output = client.chat.completions.create(model = DIAG_MODEL, 
                                                        temperature = DIAG_TEMP, 
                                                        messages = [{"role": "system", "content": secondary_prompt}, 
                                                                    {"role": "user", "content": diagnosis}])
            matched_condition = raw_output.choices[0].message.content
            print(diagnosis + ": " + matched_condition)
            if matched_condition in self.secondary_checklist:
                self.secondary_checklist[matched_condition] = True
        
        # Calculate scoring
        self.score = 0
        self.max_score = 10 # Just 10 static for now
        for condition in self.main_checklist:
            if self.main_checklist[condition]:
                self.score += self.weights["Main"][condition]
        for condition in self.secondary_checklist:
            if self.secondary_checklist[condition]:
                self.score += self.weights["Secondary"][condition]

            


class Interview:

    def __init__(self, username: str, patient: Patient):
        self.__username = username
        self.__patient = patient
        self.__messages = []
    
        # Make categories according to categories that patient has weights for
        self.__categories = []
        for category in self.__patient.weights_data:
            self.__categories.append(Category(category, patient))
        
        # Diagnosis added once user provides
    
    def add_datagrades(self):
        self.__datagrades = DataGrades(self.__patient, self.__categories, self.__messages)
    
    def add_diagnosis(self, main_diagnosis: str, main_rationale: str, secondary_diagnoses: list[str]):
        self.__diagnosis = Diagnosis(main_diagnosis, main_rationale, secondary_diagnoses)
    
    def add_diagnosisgrades(self):
        self.__diagnosisgrades = DiagnosisGrades(self.__patient, self.__diagnosis)
    
    def add_message(self, message: Message) -> None:
        if message.type and message.role and message.content:
            self.__messages.append(message)
    
    def get_username(self) -> str:
        return self.__username
    
    def get_patient(self) -> Patient:
        return self.__patient
    
    def get_messages(self) -> list[Message]:
        return self.__messages
    
    def get_categories(self):
        return self.__categories

    def get_datagrades(self):
        return self.__datagrades
    
    def get_diagnosis(self):
        return self.__diagnosis
    
    def get_diagnosisgrades(self):
        return self.__diagnosisgrades

    #TODO Where are the grades :skull:
    def get_dict(self):
        currentDateTime=date.datetime.now()
        conversation_dict={} #Wrapper dictionary
        messages_dict=[] # List of messages
        conversation_dict["date_time"]=str(currentDateTime)
        conversation_dict["username"]=self.get_username()
        conversation_dict["patient"]=self.get_patient().get_dict()
        for message in self.__messages:
            messages_dict.append(message.get_dict())
        conversation_dict["messages"]=messages_dict
        conversation_dict["data_grades"]=self.get_datagrades().get_dict()

        return conversation_dict

    def get_json(self):
        return json.dumps(self.get_dict(),indent=4)
