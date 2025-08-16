import time
from datetime import datetime
from docx import Document
import io
import os
import base64
import json
import tempfile
from annotated_text import annotated_text
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import re

from openai import OpenAI
from anthropic import Anthropic
from google import genai


def create_prompt(prompt: str, rubric: dict) -> str:
    prompt = prompt.replace("<title></title>", f"<title>{rubric['title']}</title>")
    prompt = prompt.replace("<desc></desc>", f"<desc>{rubric['desc']}</desc>")
    exclude = ['title', 'desc', 'html']
    to_insert = {k: v for k, v in rubric.items() if k not in exclude}
    prompt = prompt.replace("<rubric></rubric>", f"<rubric>{to_insert}</rubric>")

    return prompt


def extract_from_output(output: str) -> dict:

    def extract(tag: str):
        match = re.search(rf'<{tag}>([\s\S]*?)</{tag}>', output)
        if match:
            return match.group(1).strip()
        else:
            print(f"ERROR: no match for <{tag}> in output")
            return None

    reasoning = extract("reasoning")
    grade = extract("grade")
    if grade:
        try:
            grade_dict = json.loads(grade)
            features = grade_dict['features']
            score = grade_dict['score']
        except json.JSONDecodeError as e:
            print(f"ERROR: Could not parse grade JSON '{grade}': {e}")
            grade_dict = features = score = None
    else:
        grade_dict = features = score = None
    feedback = extract("feedback")

    return {
        'reasoning': reasoning,
        'grade': grade,
        'feedback': feedback
    }


def generate_openai(model: str, temperature: float, system_prompt: str, student_response: str) -> dict:
    client = OpenAI()

    # Generate output
    raw_output = client.responses.create(
            model = model,
            temperature = temperature,
            instructions = system_prompt,
            reasoning = {
                'effort': 'medium',
            },
            input = student_response
        )
    output = raw_output.output[0].content.text
    print(output)
    
    eval = extract_from_output(output) # reasoning, grade, feedback
    usage = {
        'input_tokens': raw_output.usage.input_tokens,
        'output_tokens': raw_output.usage.output_tokens
    }
    eval['usage'] = usage

    return eval


def generate_anthropic(model: str, temperature: float, system_prompt: str, student_response: str) -> dict:
    client = Anthropic()

    # Generate output
    prefill = "<reasoning>"
    raw_output = client.messages.create(
            model = model,
            temperature = temperature,
            system = system_prompt,
            thinking = {
                "type": "enabled",
                "budget_tokens": 16384
            },
            messages = [
                {"role": "user", "content": student_response},
                {"role": "assistant", "content": prefill}
            ]
        )
    output = prefill + raw_output.content[0].text
    print(output)

    eval = extract_from_output(output) # reasoning, grade, feedback
    usage = {
        'input_tokens': raw_output.usage.input_tokens,
        'output_tokens': raw_output.usage.output_tokens
    }
    eval['usage'] = usage

    return eval


def generate_google(model: str, temperature: float, system_prompt: str, student_response: str) -> dict:
    client = genai.Client()

    # Generate output
    raw_output = client.models.generate_content(
            model = model,
            config=genai.types.GenerateContentConfig(
                temperature = temperature,
                system_instruction = system_prompt,
                thinking_config = genai.types.ThinkingConfig(thinking_budget=-1) # dynamic thinking
            ),
            contents = student_response
        )
    output = raw_output.text
    print(output)

    eval = extract_from_output(output) # reasoning, grade, feedback
    usage = {
        'input_tokens': raw_output.usage_metadata.prompt_token_count,
        'output_tokens': raw_output.usage_metadata.candidates_token_count
    }
    eval['usage'] = usage

    return eval


def generate_eval(provider: str, model: str, temperature: float, system_prompt: str, student_response: str) -> dict:
    eval = None

    if provider == "openai":
        eval = generate_openai(model, temperature, system_prompt, student_response)
    elif provider == "anthropic":
        eval = generate_anthropic(model, temperature, system_prompt, student_response)
    elif provider == "google":
        eval = generate_google(model, temperature, system_prompt, student_response)

    return eval