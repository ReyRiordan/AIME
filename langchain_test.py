from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

import time
import textract
import tiktoken
import token_counter

import aspose.words as aw
from datetime import date
import export_docx


KEY = "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"
MODEL = "gpt-4"
PROMPT = "./Prompt/" + "Prompt_11-7.txt"
TOWRITE = "./Prompt/" + "output.txt"
QUESTIONS = "./Prompt/questions.txt"
QUESTIONS_OPEN = "./Prompt/questions_open.txt"

llm = ChatOpenAI(openai_api_key=KEY, model_name=MODEL, temperature=0.7)
conversation = ConversationChain(llm=llm, memory=ConversationBufferMemory())


# A list of all messages sent thusfar
allMessages = []
#Adding the prompt from the .docx file before the conversation begins
#user_input = textract.process("./Prompt/Chat_GPT_prompt_V1023_OBJ1.docx").decode()
with open(PROMPT, "r", encoding="utf8") as prompt:
    prompt_input = prompt.read()
print("Prompt length: " + str(token_counter.num_tokens_used([prompt_input])) + " tokens")

#with open(TOWRITE,"w", encoding = "utf8") as logger: 
    #logger.write(""); 

output = conversation.predict(input=prompt_input)
print("GPT: " + output + "\n")
mode = input("Select mode (AUTO / AUTO OPEN / MANUAL): ")

def auto_questioning(question_prompt, delay):
     with open(question_prompt, "r", encoding="utf8") as questions:
            while True:
                user_input = questions.readline()
                if not user_input: break
                allMessages.append(user_input)
                print("User: " + user_input)
                output = conversation.predict(input=user_input)
                allMessages.append(output)
                print("GPT: " + output + "\n")
                time.sleep(delay)

if mode == "AUTO":
    auto_questioning(QUESTIONS, 15)

elif mode == "AUTO OPEN":
    auto_questioning(QUESTIONS_OPEN, 15)

elif mode == "MANUAL":
    user_input = input("Begin the conversation: ")
    while user_input != "END":
        allMessages.append(user_input)
        output = conversation.predict(input=user_input)
        allMessages.append(output)
        print("GPT: " + output + "\n")

        print("no. tokens used: "+str(token_counter.num_tokens_used(allMessages)))
        user_input = input("User: ")

#Count number of tokens used
print("no. tokens used: "+str(token_counter.num_tokens_used(allMessages)))

# Export
export_docx.exportAsDocx(PROMPT, MODEL, allMessages)

#with open(TOWRITE,"a",encoding="utf8") as logger:
    #logger.write(output)
    #logger.write("User: "+user_input+"\n")


