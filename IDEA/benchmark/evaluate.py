import time
from datetime import datetime
from docx import Document
import io
import base64
from openai import OpenAI
import tempfile
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lookups import *
from generate import *


def evaluate_all(provider: str, model_name: str, username: str):
    # DB SETTINGS
    client = MongoClient(DB_URI)
    source = client['Benchmark']['Interviews.M2_test']
    target = client['Benchmark']['AI_Eval.M2_test']
    sim_headers = list(source.find({}, {"netid": 1, "patient": 1}))
    # MODEL SETTINGS
    model_info = {
        "provider": provider,
        "name": model_name,
        "temperature": 0.0,
        "thinking": True,
        "prompt_id": "Feedback_8-16",
        "usage": {
            "input_tokens": 0,
            "output_tokens": 0
        }
    }
    # EVAL PROMPT
    with open(f"./Prompts/{model_info['prompt_id']}.txt", 'r') as prompt_file:
        base_prompt = prompt_file.read()

    n = 0
    for header in sim_headers:
        sim = source.find_one({"_id": header['_id']})
        start_time = datetime.now().isoformat()

        sim_info = {
            "_id": sim['_id'],
            "netid": sim['netid'],
            "patient": sim['patient'], 
        }

        n += 1
        print(f"({n}/30) {sim['netid']} | {sim['patient']}")

        evaluation = {}
        post_note = sim['post_note_inputs']
        for section in RUBRIC:
            student_response = post_note[section]
            if not student_response:
                evaluation[section] = None
                continue
            
            evaluation[section] = {}
            for part, rubric in RUBRIC[section].items():
                part_eval = generate_eval(model_info, base_prompt, rubric, student_response)
                part_usage = part_eval.pop('usage')
                model_info['usage']['input_tokens'] += part_usage['input_tokens']
                model_info['usage']['output_tokens'] += part_usage['output_tokens']
                evaluation[section][part] = part_eval

        end_time = datetime.now().isoformat()
        times = {
            start_time: "start",
            end_time: "end"
        }

        final_result = {
            "username": username,
            "model_info": model_info,
            "sim_info": sim_info,
            "rubric_id": RUBRIC_ID,
            "evaluation": evaluation,
            "times": times,
        }

        target.insert_one(final_result)


def evaluate_single(provider: str, model_name: str, username: str, netid: str, patient: str):
    # DB SETTINGS
    client = MongoClient(DB_URI)
    source = client['Benchmark']['Interviews.M2_test']
    target = client['Benchmark']['AI_Eval.M2_test']
    # MODEL SETTINGS
    model_info = {
        "provider": provider,
        "name": model_name,
        "temperature": 0.0,
        "thinking": True,
        "prompt_id": "Feedback_8-16",
        "usage": {
            "input_tokens": 0,
            "output_tokens": 0
        }
    }
    # EVAL PROMPT
    with open(f"./Prompts/{model_info['prompt_id']}.txt", 'r') as prompt_file:
        base_prompt = prompt_file.read()

    start_time = datetime.now().isoformat()

    sim = source.find_one({"netid": netid, "patient": patient}) # FIND THE SINGLE
    sim_info = {
        "_id": sim['_id'],
        "netid": sim['netid'],
        "patient": sim['patient'], 
    }

    evaluation = {}
    post_note = sim['post_note_inputs']
    for section in RUBRIC:
        student_response = post_note[section]
        if not student_response:
            evaluation[section] = None
            continue
        
        evaluation[section] = {}
        for part, rubric in RUBRIC[section].items():
            part_eval = generate_eval(model_info, base_prompt, rubric, student_response)
            part_usage = part_eval.pop('usage')
            model_info['usage']['input_tokens'] += part_usage['input_tokens']
            model_info['usage']['output_tokens'] += part_usage['output_tokens']
            evaluation[section][part] = part_eval

    end_time = datetime.now().isoformat()
    times = {
        start_time: "start",
        end_time: "end"
    }

    final_result = {
        "username": username,
        "model_info": model_info,
        "sim_info": sim_info,
        "rubric_id": RUBRIC_ID,
        "evaluation": evaluation,
        "times": times,
    }

    target.insert_one(final_result)


def evaluate(type: str, provider: str, netid = None, patient = None):
    models = {
        "anthropic": {
            "name": "claude-sonnet-4-20250514",
            "username": "Claude 4S"
        },
        "openai": {
            "name": "gpt-5-2025-08-07",
            "username": "GPT 5"
        },
        "google": {
            "name": "gemini-2.5-pro",
            "username": "Gemini 2.5P"
        }
    }

    if type == "all":
        evaluate_all(
            provider = provider,
            model_name = models[provider]['name'],
            username = models[provider]['username'],
        )

    elif type == "single":
        evaluate_single(
            provider = provider,
            model_name = models[provider]['name'],
            username = models[provider]['username'],
            netid = netid,
            patient = patient
        )

    else:
        print("ERROR")


if __name__ == "__main__":
    evaluate(
        type = "single",
        provider = "google",
        netid = "mi360",
        patient = "Jeffrey Smith"
    )