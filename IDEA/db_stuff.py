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
import random


def copy_post_notes():
    client = MongoClient(DB_URI)

    sources = ["M1", "M2"]
    target_db = client["Benchmark"]["Interviews"]

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
            patient = doc["patient"]["id"]
            del doc["patient"]
            doc["patient"] = patient
            del doc["feedback"]
            doc["post_note"] = doc.pop("post_note_inputs")
            doc.pop("convo_data", None)
            doc.pop("_id", None)  # Remove _id to avoid conflict
            modified_docs.append(doc)

        if modified_docs:
            target_collection.insert_many(modified_docs)
            print(f"Copied {len(modified_docs)} documents from {source_name}")
        else:
            print(f"No documents to copy for {source_name}")

def manual_filter():
    client = MongoClient(DB_URI)
    source = client["Benchmark"]["Interviews"]["M2"]

    docs = list(source.find({}, {"netid": 1, "patient": 1, "post_note": 1}))

    for doc in docs:
        print("---------------------------------------------------------------------")
        print("post_note:", doc.get("post_note", "[No post_note]"))
        response = input("Keep this doc? (y/n): ").strip().lower()
        if response == "n":
            source.delete_one({"_id": doc["_id"]})

def select_eval_set():
    client = MongoClient(DB_URI)
    source = client["Benchmark"]["Interviews"]["M2"]
    eval_test = client["Benchmark"]["Interviews"]["M2_test"]
    eval_rem = client["Benchmark"]["Interviews"]["M2_rem"]

    # retrieve all and random shuffle
    all_docs = list(source.find())
    random.shuffle(all_docs)

    # split into groups by patient
    groups = {"Jeffrey Smith": [],
              "Jenny Smith": [],
              "Samuel Thompson": [],
              "Sarah Thompson": []}
    for doc in all_docs:
        groups[doc["patient"]].append(doc)

    # select 40 (10 for each patient, all unique students)
    selected = []
    used = set()
    for patient, docs in groups.items():
        group_selected = []
        for doc in docs:
            if doc["netid"] not in used:
                group_selected.append(doc)
                used.add(doc["netid"])
            if len(group_selected) == 10:
                break
        selected.extend(group_selected)

    # get remaining
    selected_ids = {doc["_id"] for doc in selected}
    remaining = [doc for doc in all_docs if doc["_id"] not in selected_ids]
    
    # store each
    for doc in selected:
        doc.pop("_id", None)
    eval_test.insert_many(selected)
    for doc in remaining:
        doc.pop("_id", None)
    eval_rem.insert_many(remaining)

def add_sexes():
    client = MongoClient(DB_URI)
    source = client['Benchmark']['Interviews.M2']
    all_docs = list(source.find())

    with open('IDEA/assignments/M2.json', 'r') as M2_file:
        M2 = json.load(M2_file)

    for doc in all_docs:
        info = M2[doc['netid']]
        doc['sex'] = info['sex']
        doc['post_note_inputs'] = doc['post_note']
        del doc['post_note']
        source.replace_one({'_id': doc['_id']}, doc)


add_sexes()