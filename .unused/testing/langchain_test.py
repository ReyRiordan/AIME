from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

import time
import tiktoken
import token_counter as token_counter

#import aspose.words as aw
import datetime as date
#import testing.export_docx as export_docx

import os
import sys
sys.path.append('/Users/reyriordan/Documents/Research/Artificial-Intelligence-in-Medical-Education-AIME-/')
from webapp.lookups import *
from webapp.web_methods import *

KEY = os.getenv("OPENAI_API_KEY")
#MODEL = "gpt-4-0125-preview"
INPUT_CLASSIFY = "./Prompts/classtest_gen.txt"
BASE = "./Prompts/Base_1-15.txt"
CONTEXT = "./Prompts/JohnSmith_sectioned.txt"
#TOWRITE = "./testing/output.txt"
QUESTIONS = "./Prompts/questions.txt"
EDGE_CASES = "./Prompts/edge_cases.txt"
patient_name = "John Smith"

# llm = ChatOpenAI(openai_api_key=KEY, model_name=MODEL, temperature=0.0)
# conversation = ConversationChain(llm=llm, memory=ConversationBufferMemory())

# A list of all messages sent thusfar
# allMessages = []
# messages = []

#Adding the prompt from the .docx file before the conversation begins
#user_input = textract.process("./Prompt/Chat_GPT_prompt_V1023_OBJ1.docx").decode()
# with open(BASE, "r", encoding="utf8") as base_file:
#     base = base_file.read()
#     base = base.replace("{patient}", patient_name)
# with open(CONTEXT, "r", encoding="utf8") as context_file:
#     context = context_file.read()
# prompt_input = str(base + context)
# with open(CLASSIFY, "r", encoding="utf8") as classification_file:
#      prompt_input = classification_file.read()
messages = []
with open(INPUT_CLASSIFY, "r", encoding="utf8") as input_classify:
     while True:
          question = input_classify.readline()
          if not question: break
          messages.append(question)
# for message in messages:
#      message = message.rstrip() + " "
#      prompt_input += message
classifications = classifier(CLASSIFY_GEN_PROMPT, messages, KEY)
for index, message in enumerate(messages):
     print(message.rstrip() + ": " + str(classifications[index]) + "\n")
# print("Prompt length: " + str(token_counter.num_tokens_used([prompt_input])) + " tokens")

#with open(TOWRITE,"w", encoding = "utf8") as logger: 
    #logger.write(""); 

# output = conversation.predict(input=prompt_input)
# print("GPT: " + output + "\n")
# mode = input("Select mode (AUTO / EDGE / MANUAL): ")

# def auto_questioning(question_prompt, delay):
#      with open(question_prompt, "r", encoding="utf8") as questions:
#             while True:
#                 user_input = questions.readline()
#                 if not user_input: break
#                 messages.append({"role" : "User", "content" : user_input.strip()})
#                 allMessages.append(user_input)
#                 print("User: " + user_input)
#                 output = conversation.predict(input=user_input)
#                 messages.append({"role" : "Patient", "content" : output})
#                 allMessages.append(output)
#                 print("GPT: " + output + "\n")
#                 time.sleep(delay)

# if mode == "AUTO":
#     auto_questioning(QUESTIONS, 15)

# elif mode == "EDGE":
#     auto_questioning(EDGE_CASES, 5)

# elif mode == "MANUAL":
#     user_input = input("Begin the conversation: ")
#     while user_input != "END":
#         messages.append({"role" : "User", "content" : user_input.strip()})
#         allMessages.append(user_input)
#         output = conversation.predict(input=user_input)
#         messages.append({"role" : "Patient", "content" : output})
#         allMessages.append(output)
#         print("GPT: " + output + "\n")

#         print("no. tokens used: "+str(token_counter.num_tokens_used(allMessages)))
#         user_input = input("User: ")

# #Count number of tokens used
# print("no. tokens used: "+str(token_counter.num_tokens_used(allMessages)))

# # Export
# interview = create_interview_file("TEST", "John Smith", messages)
# interview.save("./testing/interview.docx")

#with open(TOWRITE,"a",encoding="utf8") as logger:
    #logger.write(output)
    #logger.write("User: "+user_input+"\n")


