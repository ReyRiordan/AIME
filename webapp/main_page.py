from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
import time
import datetime as date
from docx import Document
import io
import streamlit as st

st.title("Medical Interview Simulation")

if "stage" not in st.session_state:
    st.session_state["stage"] = 0

def set_stage(stage):
    st.session_state["stage"] = stage


if st.session_state["stage"] == 0:
    st.session_state["username"] = st.text_input("Enter a username (does not have to be your real name):")
    if st.session_state["username"]:
        password = st.text_input("Enter user password:")
        if password == "corbett": 
            st.write("Authentication successful!")
            time.sleep(2)
            set_stage(1)
            st.rerun()


if st.session_state["stage"] == 1:
    st.session_state["messages"] = []
    st.session_state["patient"] = st.selectbox("Which patient would you like to interview?", 
                                               ["John Smith"],
                                               index = None,
                                               placeholder = "Select patient...")

    st.button("Start conversation", on_click=set_stage, args=[2])


if st.session_state["stage"] == 2:
    prompt_input = "default prompt"
    if st.session_state["patient"] == "John Smith":
        PROMPT = "./Prompt/Prompt_11-7.txt"
        with open(PROMPT, 'r', encoding='utf8') as prompt:
            prompt_input = prompt.read()

    KEY = ""
    MODEL = "gpt-4"
    llm = ChatOpenAI(openai_api_key=KEY, model_name=MODEL, temperature=0.7)
    st.session_state["conversation"] = ConversationChain(llm=llm, memory=ConversationBufferMemory())
    initial_output = st.session_state["conversation"].predict(input=prompt_input)

    st.session_state["messages"].append({"role": "assistant", "content": "You may now begin your interview with " + st.session_state["patient"] + "."})
    
    set_stage(3)


if st.session_state["stage"] == 3:
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if user_input := st.chat_input("Type here..."):
        with st.chat_message(st.session_state["username"]):
            st.markdown(user_input)
        st.session_state["messages"].append({"role": st.session_state["username"], "content": user_input})
        output = st.session_state["conversation"].predict(input=user_input)
        with st.chat_message(st.session_state["patient"]):
            st.markdown(output)
            st.session_state["messages"].append({"role": st.session_state["patient"], "content": output})

    st.button("End conversation", on_click=set_stage, args=[4])


if st.session_state["stage"] == 4:
    bio = io.BytesIO()
    doc = Document()
    heading = doc.add_paragraph("User: " + st.session_state["username"] + ", ")
    currentDateAndTime = date.datetime.now()
    date_time = currentDateAndTime.strftime("%d-%m-%y__%H-%M")
    heading.add_run("Date: " + date_time + ", ")
    heading.add_run("Patient: " + st.session_state["patient"])
    for message in st.session_state["messages"]:
        doc.add_paragraph(message["role"] + ": " + message["content"])
    doc.save(bio)
    st.download_button("Download interview", 
                        data=bio.getvalue(),
                        file_name=st.session_state["username"]+"_"+date_time+".docx",
                        mime="docx")
    st.button("New interview", on_click=set_stage, args=[1])

    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

