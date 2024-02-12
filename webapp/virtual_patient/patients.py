from langchain_community.chat_models import ChatOpenAI
from langchain.chains.conversation.base import ConversationChain
from langchain.memory.buffer import ConversationBufferMemory
from virtual_patient.paths import *

class GPT_Patient:

    def __init__(self, name):
        # Assign name of patient
        self.name = name

        # Create virtual patient prompt
        with open(BASE_PATH, "r", encoding="utf8") as base_prompt:
            base = base_prompt.read()
        with open(cases[name][0], "r", encoding="utf8") as case_prompt:
            case = case_prompt.read()
        self.initial_input = str(base + case)

        # Assign physical and ECG data paths for patient for website display use
        self.physical_path = "./Patient_Info/Physical_" + self.name.replace(" ", "") + ".docx"
        self.ECG_path = "./Patient_Info/ECG_" + self.name.replace(" ", "") + ".png"

        # Extract all asoc and risk label descriptions for later use
        asoc_label_descs = {}
        with open(ASOC_PATH, "r", encoding="utf8") as asoc_desc:
            while True: 
                line = asoc_desc.readline()
                if not line: break
                line = line.rstrip()
                linesplit = line.split("||")
                asoc_label_descs[linesplit[0]] = linesplit[1]
        risk_label_descs = {}
        with open(RISK_PATH, "r", encoding="utf8") as risk_desc:
            while True: 
                line = risk_desc.readline()
                if not line: break
                line = line.rstrip()
                linesplit = line.split("||")
                risk_label_descs[linesplit[0]] = linesplit[1]
        
        # Extract asoc and risk label weights for patient
        self.weights_asoc = {}
        with open(cases[name][1], "r", encoding="utf8") as asoc_prompt:
            while True:
                line = asoc_prompt.readline()
                if not line: break
                line = line.rstrip()
                linesplit = line.split(" ")
                self.weights_asoc[linesplit[0]] = int(linesplit[1])
        self.weights_risk = {}
        with open(cases[name][2], "r", encoding="utf8") as risk_prompt:
            while True:
                line = risk_prompt.readline()
                if not line: break
                line = line.rstrip()
                linesplit = line.split(" ")
                self.weights_risk[linesplit[0]] = int(linesplit[1])

        # Create classify assoc and risk prompts for patient
        with open(CLASS_ASOC_PATH, "r", encoding="utf8") as base_asoc_prompt:
            asoc_base = base_asoc_prompt.read()
            asoc_base = asoc_base.split("|PATIENT DEPENDENT|")
            self.class_asoc_prompt = asoc_base[0]
            for label in self.weights_asoc:
                self.class_asoc_prompt += "[" + label + "]\nAny question about " + asoc_label_descs[label] + "\n"
            self.class_asoc_prompt += asoc_base[1]
        with open(CLASS_RISK_PATH, "r", encoding="utf8") as base_risk_prompt:
            risk_base = base_risk_prompt.read()
            risk_base = risk_base.split("|PATIENT DEPENDENT|")
            self.class_risk_prompt = risk_base[0]
            for label in self.weights_risk:
                self.class_risk_prompt += "[" + label + "]\nAny question about " + risk_label_descs[label] + "\n"
            self.class_risk_prompt += risk_base[1]

        # Extract gen and dims label weights (not patient specific for now)
        self.weights_gen = WEIGHTS_GEN
        self.weights_dims = WEIGHTS_DIMS