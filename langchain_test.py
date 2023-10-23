from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory

KEY = "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"
MODEL = "gpt-4"

llm = ChatOpenAI(openai_api_key=KEY, model_name=MODEL)
conversation = ConversationChain(llm=llm, memory=ConversationBufferMemory())

user_input = input("START: ")
while user_input != "END":
    print("GPT:" + conversation.predict(input=user_input) + "\n")
    user_input = input("User: ")

