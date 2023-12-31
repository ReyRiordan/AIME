from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
import time
import datetime as date
from docx import Document
import io
import os
import streamlit as st

os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
os.environ["LOGIN_PASS"] = st.secrets["LOGIN_PASS"]
LOGIN_PASS = os.getenv("LOGIN_PASS")

PHYSICAL_LOCATION = "./Patient_Info/Physical_JohnSmith.docx"
ECG_LOCATION = "./Patient_Info/ECG_JohnSmith.png"

st.title("Medical Interview Simulation")

if "stage" not in st.session_state:
    st.session_state["stage"] = 0

def set_stage(stage):
    st.session_state["stage"] = stage


if st.session_state["stage"] == 0:
    st.write("""Welcome! Thank you for agreeing to try out this virtual patient interview platform. Once you log in and get started, 
             there will be a chat interface where you can interview a virtual patient AI acting as a patient in a specific case study. 
             The goal is to interview the patient as if it was a real patient in order to work towards a diagnosis. The AI's 
             conversational responses to your questions may include expressions of worry and we hope that you respond as if it was a real patient.""")
    st.write("""We are working on developing a feedback rubric that will evaluate the virtual patient interaction with regard to clinical reasoning
             (e.g. general data gathering, evidence of hypothesis-driven questions, and data interpretation) as well as empathy and clarity. 
             Once you have completed the interview, we would apprciate any feedback regarding the nature of the responses themselves 
             (any responses that went off the rails) and their appropriateness to the questions that you asked. We would also appreciate 
             any feedback on how the interaction may be improved or made more realistic (responses seem too rote, a normal patient wouldn't 
             use these words, etc). Thank you in advance; please follow the instructions below to log in and get started!""")
    
    st.session_state["username"] = st.text_input("Enter any username (does not have to be your real name) and press \"Enter\":")
    if st.session_state["username"]:
        password = st.text_input("Enter the password you were provided and press \"Enter\":")
        if password == LOGIN_PASS: 
            st.write("Authentication successful!")
            time.sleep(2)
            set_stage(1)
            st.rerun()


if st.session_state["stage"] == 1:
    st.write("""This is the patient selection screen. Currently we only have one patient (case study) option, but we hope to expand this further
             in the future. For now, please just select "John Smith" as your patient and click the "Start Interview" button when you are 
             ready to begin.""")
    
    st.session_state["messages"] = []
    st.session_state["patient"] = st.selectbox("Which patient would you like to interview?", 
                                               ["John Smith"],
                                               index = None,
                                               placeholder = "Select patient...")

    st.button("Start Interview", on_click=set_stage, args=[2])


if st.session_state["stage"] == 2:
    prompt_input = "default prompt"
    if st.session_state["patient"] == "John Smith":
        PROMPT = "./Prompt/Prompt_11-7.txt"
        with open(PROMPT, 'r', encoding='utf8') as prompt:
            prompt_input = prompt.read()

    MODEL = "gpt-4"
    llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model_name=MODEL, temperature=0.0)
    st.session_state["conversation"] = ConversationChain(llm=llm, memory=ConversationBufferMemory())
    initial_output = st.session_state["conversation"].predict(input=prompt_input)

    st.session_state["messages"].append({"role": "assistant", "content": "You may now begin your interview with " + st.session_state["patient"] + "."})
    
    set_stage(3)


if st.session_state["stage"] == 3:
    st.write("""This is the chat interface where you can interview your virtual patient. You may type your message to your patient 
             in the text box at the bottom of your screen, and either press \"Enter\" or click the paper airplane button when your message 
             is ready to be sent. The virtual patient should then respond to your message. Please treat this as a real medical interview, 
             imagining that you have just walked into a room where this patient was waiting. When you are satisfied, click the \"End Interview\" 
             button to move on to the next screen.""")
    
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

    st.button("End Interview", on_click=set_stage, args=[4])


if st.session_state["stage"] == 4:
    st.session_state["interview"] = Document()
    heading = st.session_state["interview"].add_paragraph("User: " + st.session_state["username"] + ", ")
    currentDateAndTime = date.datetime.now()
    date_time = currentDateAndTime.strftime("%d-%m-%y__%H-%M")
    heading.add_run("Date: " + date_time + ", ")
    heading.add_run("Patient: " + st.session_state["patient"])
    for message in st.session_state["messages"]:
        st.session_state["interview"].add_paragraph(message["role"] + ": " + message["content"])
    st.session_state["interview"].save("./Conversations/" + st.session_state["username"]+"_"+date_time+".docx")
    
    set_stage(5)

if st.session_state["stage"] == 5:
    st.write("""Thank you so much for completing your interview! A record of the interview has been sent to us. If you would like, you may 
             view a physical examination and ECG corresponding for the patient in order to get a clearer potential differential diagnosis 
             in your mind. You may also click the \"Download Interview\" button to save a copy for yourself as a docx file. After receiving 
             feedback from helpful people like you, we plan to add a screen where you can enter your diagonsis and get feedback on it.""")
    
    st.button("View Physical", on_click=set_stage, args=[6])
    st.button("View ECG", on_click=set_stage, args=[7])

    currentDateAndTime = date.datetime.now()
    date_time = currentDateAndTime.strftime("%d-%m-%y__%H-%M")
    bio = io.BytesIO()
    st.session_state["interview"].save(bio)
    st.download_button("Download interview", 
                        data=bio.getvalue(),
                        file_name=st.session_state["username"]+"_"+date_time+".docx",
                        mime="docx")
    st.button("New interview", on_click=set_stage, args=[1])

    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if st.session_state["stage"] == 6:
    st.header("Physical Examination Findings")
    st.write("Here is the full physical examination for " + st.session_state["patient"] + ". Click the \"Back\" button to go back once you're done.")
    physical_exam_doc = Document(PHYSICAL_LOCATION)
    for parargraph in physical_exam_doc.paragraphs:
        st.write(parargraph.text)
    st.button("Back", on_click=set_stage, args=[5])
    

if st.session_state["stage"] == 7:
    st.header("ECG Chart")
    st.write("Here is the ECG for " + st.session_state["patient"] + ". Click the \"Back\" button to go back once you're done.")
    st.image(ECG_LOCATION)
    st.button("Back", on_click=set_stage, args=[5])