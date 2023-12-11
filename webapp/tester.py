from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
import time
import datetime as date
from docx import Document 
import io
import streamlit as st
import base64

INTRODUCTORY_MESSAGE_LOCATION = '../Prompt/Website_introduction.docx'
introductory_msg = Document(INTRODUCTORY_MESSAGE_LOCATION)
print(introductory_msg.paragraphs[1].text)