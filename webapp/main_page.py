from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
import time
import datetime as date
from docx import Document
import docx as docx
import os
import io
import streamlit as st

st.title("Medical Interview Simulation")


# @REY: Instead of writing down numbers, make each one of those numbers
#       into its own variable for easy on-the-fly changing. I did the first
#       one but I'm mad lazy so u got the rest. It's out of order right now, 
#       but once they're all named, u can then easily swap 'em around. Good
#       programming practice. 


# All page indices
LOGIN_PAGE = 0
INTRODUCTORY_INFO_PAGE = 5
PHYSICAL_EXAMINATION = 6

#All relevant directories
PROMPT = "./Prompt/Prompt_11-7.txt" #all globals and constants are declared at the start
INTRODUCTORY_MESSAGE_LOCATION = "./Medical_Info/Website_introduction.docx"
PHYSICAL_EXAMINATION_LOCATION = "./Medical_Info/Physical_examination_for_first_test_case.docx"
ECG_LOCATION = "./Medical_Info/ecg.png"


if "stage" not in st.session_state:
    st.session_state["stage"] = LOGIN_PAGE

def set_stage(stage):
    st.session_state["stage"] = stage


if st.session_state["stage"] == LOGIN_PAGE:
    st.session_state["username"] = st.text_input("Enter a username (does not have to be your real name):")
    if st.session_state["username"]:
        password = st.text_input("Enter user password:")

        os.environ["PWORD"] = st.secrets["PWORD"]
        legit_password = os.getenv("PWORD")

        if password == legit_password: 
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

    st.button("Confirm choice", on_click=set_stage, args=[INTRODUCTORY_INFO_PAGE])


if st.session_state["stage"]==INTRODUCTORY_INFO_PAGE: 
    introductory_msg = Document(INTRODUCTORY_MESSAGE_LOCATION)
    for parargraph in introductory_msg.paragraphs:
        st.write(parargraph.text)
    st.button("Proceed to interview", on_click=set_stage, args=[2])



if st.session_state["stage"] == 2:
    prompt_input = "default prompt"
    if st.session_state["patient"] == "John Smith":
        with open(PROMPT, 'r', encoding='utf8') as prompt:
            prompt_input = prompt.read()

    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
    KEY = os.getenv("OPENAI_API_KEY")
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

    st.button("End conversation", on_click=set_stage, args=[PHYSICAL_EXAMINATION])

if st.session_state["stage"]==PHYSICAL_EXAMINATION:
    physical_exam_doc = Document(PHYSICAL_EXAMINATION_LOCATION)
    st.header("Physical Examination Findings")
    for parargraph in physical_exam_doc.paragraphs:
        st.write(parargraph.text)
    st.header("ECG Chart")
    st.image(ECG_LOCATION)
    st.button("Proceed to diagnosis and end screen", on_click=set_stage, args=[4])
    

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

