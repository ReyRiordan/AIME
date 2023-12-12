from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
import time
import datetime as date
from docx import Document
import io
import os
import streamlit as st
import streamlit.components.v1 as components
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName,
    FileType, Disposition, ContentId)

# PAGE INFORMATION
LOGIN_PAGE = 0
PATIENT_SELECTION = 1
PATIENT_LOADING = 2
CHAT_INTERFACE = 3
CREATE_INTERVIEW_FILE = 4
POST_INTERVIEW = 5
PHYSICAL_SCREEN = 6
ECG_SCREEN = 7
FEEDBACK_SCREEN = 8
FINAL_SCREEN = 9

# FILE LOCATIONS
PHYSICAL_LOCATION = "./Patient_Info/Physical_JohnSmith.docx"
ECG_LOCATION = "./Patient_Info/ECG_JohnSmith.png"

BASE_PROMPT = "./Prompt/Base_12-11.txt"
prompts = {
    "John Smith" : "./Prompt/JohnSmith_12-11.txt",
    "Jackie Smith" : "./Prompt/JackieSmith_12-11.txt"
}

# EMAIL API
EMAILS_TO_SEND = [('rutgers.aime@gmail.com')]

os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
os.environ["LOGIN_PASS"] = st.secrets["LOGIN_PASS"]
LOGIN_PASS = os.getenv("LOGIN_PASS")


st.title("Medical Interview Simulation")

if "stage" not in st.session_state:
    st.session_state["stage"] = LOGIN_PAGE

def set_stage(stage):
    st.session_state["stage"] = stage

def send_email(bio):
    if st.session_state["has_sent_email"]==False:
        st.session_state["has_sent_email"]=True
        message = Mail(
            from_email='rutgers.aime@gmail.com',
            to_emails= EMAILS_TO_SEND,
            subject='Conversation from '+st.session_state["username"]+" at time "+date_time,
            html_content=st.session_state["feedback_string"])
        attachment = Attachment()
        encoded = base64.b64encode(bio.getvalue()).decode()
        attachment.file_content=FileContent(encoded)
        attachment.file_type = FileType('docx')
        attachment.file_name = FileName(st.session_state["username"]+"_"+date_time+".docx")
        attachment.disposition = Disposition('attachment')
        attachment.content_id = ContentId('docx')
        message.attachment = attachment
        try:
            sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
            response = sg.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
        except: 
            print("ERROR ENCOUNTERED SENDING MESSAGE\n")

if st.session_state["stage"] == LOGIN_PAGE:
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
            set_stage(PATIENT_SELECTION)
            st.rerun()


if st.session_state["stage"] == PATIENT_SELECTION:
    st.write("""This is the patient selection screen. Please select a patient of your choice and click the "Start Interview" button when you are 
             ready to begin.""")
    
    st.session_state["messages"] = []
    st.session_state["patient"] = st.selectbox("Which patient would you like to interview?", 
                                               ["John Smith", "Jackie Smith"],
                                               index = None,
                                               placeholder = "Select patient...")

    st.button("Start Interview", on_click=set_stage, args=[PATIENT_LOADING])


if st.session_state["stage"] == PATIENT_LOADING:
    with open(BASE_PROMPT, 'r', encoding='utf8') as base:
        base_prompt = base.read()
    INFO = prompts[st.session_state["patient"]]
    with open(INFO, 'r', encoding='utf8') as info:
        patient_info = info.read()
    prompt_input = str(base_prompt + patient_info)

    MODEL = "gpt-4"
    llm = ChatOpenAI(openai_api_key=OPENAI_API_KEY, model_name=MODEL, temperature=0.0)
    st.session_state["conversation"] = ConversationChain(llm=llm, memory=ConversationBufferMemory())
    initial_output = st.session_state["conversation"].predict(input=prompt_input)

    st.session_state["messages"].append({"role": "Assistant", "content": "You may now begin your interview with " + st.session_state["patient"] + "."})
    
    set_stage(CHAT_INTERFACE)


if st.session_state["stage"] == CHAT_INTERFACE:
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

    st.button("End Interview", on_click=set_stage, args=[CREATE_INTERVIEW_FILE])


if st.session_state["stage"] == CREATE_INTERVIEW_FILE:
    st.session_state["interview"] = Document()
    heading = st.session_state["interview"].add_paragraph("User: " + st.session_state["username"] + ", ")
    currentDateAndTime = date.datetime.now()
    date_time = currentDateAndTime.strftime("%d-%m-%y__%H-%M")
    heading.add_run("Date: " + date_time + ", ")
    heading.add_run("Patient: " + st.session_state["patient"])
    for message in st.session_state["messages"]:
        st.session_state["interview"].add_paragraph(message["role"] + ": " + message["content"])
    st.session_state["interview"].save("./Conversations/" + st.session_state["username"]+"_"+date_time+".docx")

    #We haven't sent the interview file yet, so set to false
    
    st.session_state["has_sent_email"]=False
    
    #Set stage to POST_INTERVIEW
    set_stage(POST_INTERVIEW)

if st.session_state["stage"] == POST_INTERVIEW:
    
    st.write("""Thank you for completing your interview! At this stage, you may view a physical
            examination and ECG corresponding for the patient in order to get a clearer potential differential
            diagnosis in your mind. Once you have a potential diagnosis in mind, click \"Provide Your Diagnosis\" 
            to proceed further. """)
    

    st.button("View Physical", on_click=set_stage, args=[PHYSICAL_SCREEN])
    st.button("View ECG", on_click=set_stage, args=[ECG_SCREEN])
    st.button("Provide Your Diagnosis", on_click=set_stage, args=[FEEDBACK_SCREEN])

if st.session_state["stage"] == PHYSICAL_SCREEN:
    st.header("Physical Examination Findings")
    st.write("Here is the full physical examination for " + st.session_state["patient"] + ". Click the \"Back\" button to go back once you're done.")
    physical_exam_doc = Document(PHYSICAL_LOCATION)
    for parargraph in physical_exam_doc.paragraphs:
        st.write(parargraph.text)
    st.button("Back", on_click=set_stage, args=[POST_INTERVIEW])
    

if st.session_state["stage"] == ECG_SCREEN:
    st.header("ECG Chart")
    st.write("Here is the ECG for " + st.session_state["patient"] + ". Click the \"Back\" button to go back once you're done.")
    st.image(ECG_LOCATION)
    st.button("Back", on_click=set_stage, args=[POST_INTERVIEW])

if st.session_state["stage"]==FEEDBACK_SCREEN:
    st.session_state["feedback_string"] = st.text_input(""" Once you are ready, please take the time to give us some feedback in the text box provided.
                                        What's your diagnosis of the patient?
                                        Were there any responses that the AI gave that you felt were unrealistic or problematic (specific examples)?
                                        Are there any fixes, improvements, or additional features you have in mind before you would consider this to
                                        be a good practice tool for students? 
                                        After you are done, please click the \"Send Feedback\" button and a copy of your feedback and interview will automatically be emailed to us.
                                        Thank you again!""")
    st.session_state["feedback_string"] = "<p> "+st.session_state["feedback_string"]+" </p>"
    st.button("Go to End Screen", on_click=set_stage, args=[FINAL_SCREEN])

if st.session_state["stage"] == FINAL_SCREEN: 

    st.write("""Thank you so much for completing your interview! A record of the interview has been sent to us. You may also click the \"Download Interview\" 
             button to save a copy for yourself as a docx file. After receiving feedback from helpful people like you, we plan to add an automated diagnosis
             evaluation engine. Thank you once again for your time, and we look forward to having you again.""")


    # Getting current date and time for bookkeeping purposess 
    currentDateAndTime = date.datetime.now()
    date_time = currentDateAndTime.strftime("%d-%m-%y__%H-%M")

    # Setting up file for attachment sending
    bio = io.BytesIO()
    st.session_state["interview"].save(bio)
    send_email(bio)
    
    # Download button
    st.download_button("Download interview", 
                        data=bio.getvalue(),
                        file_name=st.session_state["username"]+"_"+date_time+".docx",
                        mime="docx")
    
    st.button("New interview", on_click=set_stage, args=[PATIENT_SELECTION])
    
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])