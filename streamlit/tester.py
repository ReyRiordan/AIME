INFO = "./Prompt/JackieSmith_12-11.txt"
BASE = "./Prompt/Base_12-11.txt"

with open(BASE, 'r', encoding='utf8') as base:
    base_prompt = base.read()
with open(INFO, 'r', encoding='utf8') as info:
    patient_info = info.read()
print(str(base_prompt + patient_info))