from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

import textract
import tiktoken
import token_counter

KEY = "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"
MODEL = "gpt-4"

llm = ChatOpenAI(openai_api_key=KEY, model_name=MODEL)
conversation = ConversationChain(llm=llm, memory=ConversationBufferMemory())


# A list of all messages sent thusfar
allMessages = []
#Adding the prompt from the .docx file before the conversation begins
user_input = textract.process("./Prompt/Chat_GPT_prompt_V1023_OBJ1.docx").decode()
allMessages.append(user_input)

while user_input != "END":
    print("GPT:" + conversation.predict(input=user_input) + "\n")
    user_input = input("User: ")
    allMessages.append(user_input)
    #Count number of tokens used
    print("no. tokens used: "+str(token_counter.num_tokens_used(allMessages)))
