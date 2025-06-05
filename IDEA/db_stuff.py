import time
from datetime import datetime
from docx import Document
import io
import os
import streamlit as st
import streamlit.components.v1 as components
# import streamlit_authenticator as auth
import base64
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail, Attachment, FileContent, FileName,
    FileType, Disposition, ContentId)
from audiorecorder import audiorecorder
from openai import OpenAI
import tempfile
from annotated_text import annotated_text
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from lookups import *
from web_classes import *
from web_methods import *
import pytz


def copy_filtered_interviews():
    client = MongoClient(DB_URI)

    sources = ["M1", "M2"]
    target_db = client["Benchmark"]

    for source_name in sources:
        source_collection = client[source_name]["Interviews"]
        target_collection = target_db[source_name]

        # Filter where feedback is not null
        filtered_docs = source_collection.find({
            "feedback": {"$ne": None}
        })

        # Add "group" (M1/M2), change "username" to "netid"
        modified_docs = []
        for doc in filtered_docs:
            doc["group"] = source_name
            doc["netid"] = doc["username"]
            del doc["username"]
            doc.pop("_id", None)  # Remove _id to avoid conflict
            modified_docs.append(doc)

        if modified_docs:
            target_collection.insert_many(modified_docs)
            print(f"Copied {len(modified_docs)} documents to Benchmark.{source_name}")
        else:
            print(f"No documents to copy for {source_name}")

copy_filtered_interviews()
