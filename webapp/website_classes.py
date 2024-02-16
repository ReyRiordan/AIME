from lookups import *
import json

class Patient:

    def __init__(self, name):
        # Assign name of patient
        self.name = name

        # Create virtual patient prompt
        with open(PATIENTS[name]["base"], "r", encoding="utf8") as base_prompt:
            base = base_prompt.read()
        with open(PATIENTS[name]["case"], "r", encoding="utf8") as case_prompt:
            case = case_prompt.read()
        self.convo_prompt = str(base + case)

        # Assign physical and ECG data paths for patient for website display use
        self.physical = PATIENTS[name]["physical"]
        self.ECG = PATIENTS[name]["ECG"]

        # Extract labels and weights for patient
        with open(PATIENTS[name]["weights"], "r") as weights_json:
            self.weights = json.load(weights_json)


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
        for label in patient.weights[name]:
            self.used_label_descs[label] = self.all_label_descs[label]
        
        self.class_prompt = base_split[0]
        for label in self.used_label_descs:
            self.class_prompt += "[" + label.replace(" ", "_") + "] " + self.used_label_descs[label] + "\n"
        self.class_prompt += base_split[1] + self.example + base_split[2]
        

class Message:

    def __init__(self, type: str, role: str, content: str):
        self.type = type
        self.role = role
        self.content = content
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


class Grades:

    def __init__(self, patient: Patient, categories: list[Category], messages: list[Message]):
        self.patient = patient
        self.categories = categories
        
        # Initialize all grades for each category to label: False
        self.label_grades = {} # dict[str, dict[str, bool]]
        for category in categories:
            self.label_grades[category.name] = {label: False for label in patient.weights[category.name]}

        # Iterate through messages and update grades
        for message in messages:
            for category in categories:
                if category.name in message.labels:
                    labels = message.labels[category.name]
                    for label in labels:
                        self.label_grades[category.name][label] = True
        
    def get_score(self, category: Category) -> int:
        # Get weights from patient and grades from self
        weights = self.patient.weights[category.name]
        label_grades = self.label_grades[category.name]

        # Calculate score from weights and grades
        score = 0
        for label in weights:
            if label_grades[label]: 
                score += weights[label]
        
        return score
    
    def get_maxscore(self, category: Category) -> int:
        # Get weights from patient
        weights = self.patient.weights[category.name]

        # Calculate max score from weights
        max = 0
        for label in weights:
            max += weights[label]
        
        return max


class Interview:
    #TODO Make all data private and use helper methods for access and modification
    def __init__(self, username: str, patient: Patient):
        self.__username = username
        self.__patient = patient
        self.__messages = []
    
        # Make categories according to categories that patient has weights for
        self.__categories = []
        for category in self.__patient.weights:
            self.__categories.append(Category(category, patient))
    
    def add_grades(self):
        self.__grades = Grades(self.__patient, self.__categories, self.__messages)
    
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
    
    def get_grades(self):
        return self.__grades