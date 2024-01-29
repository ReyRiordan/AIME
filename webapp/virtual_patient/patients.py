from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from virtual_patient.paths import *

class GPT_patient:

    def __init__(self, name):
        self.name = name

        with open(BASE_PATH, 'r', encoding='utf8') as base_prompt:
            base = base_prompt.read()
        with open(cases[name], 'r', encoding='utf8') as case_prompt:
            case = case_prompt.read()
        self.initial_input = str(base + case)

        self.physical_path = "./Patient_Info/Physical_" + self.name.replace(" ", "") + ".docx"
        self.ECG_path = "./Patient_Info/ECG_" + self.name.replace(" ", "") + ".png"