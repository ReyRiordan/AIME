from lookups import *
import json

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

        # Extract labels and weights for patient
        with open(PATIENTS[name]["weights"], "r") as weights_json:
            self.weights = json.load(weights_json)

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
        patient_dict["weights"]=self.weights
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
        for label in patient.weights[name]:
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

#TODO Where are the grades :skull:
    def get_dict(self):
        conversation_dict={} #Wrapper dictionary
        messages_dict=[] # List of messages

        conversation_dict["username"]=self.get_username()
        conversation_dict["patient"]=self.get_patient().get_dict()
        for message in self.__messages:
            messages_dict.append(message.get_dict())
        conversation_dict["messages"]=messages_dict

        return conversation_dict

    def get_json(self):
        return json.dumps(self.get_dict(),indent=4)
