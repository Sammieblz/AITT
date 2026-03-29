"""
[AWS] Interview API — calls the SageMaker endpoint and saves results to DynamoDB.

This is the backend the frontend team calls. Run locally for testing:
    python cloud-services/api.py

POST /interview
    Request:  { "session_id": "abc123", "turn_index": 1, "question": "...", "answer": "...", "category": "teamwork", "level": "intern" }
    Response: { "session_id", "feedback", "scores", "interviewer_text", "follow_up_question", "follow_up_intent" }

GET /session/<session_id>
    Response: [ { turn_index, question, answer, scores, feedback, ... }, ... ]
"""

import os
import re
import json
import uuid
import boto3
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from dynamodb import save_turn, get_session_turns

load_dotenv()

app = Flask(__name__)

ENDPOINT_NAME = os.getenv("SM_ENDPOINT_NAME", "aitt-behavioral-endpoint")
REGION        = os.getenv("AWS_DEFAULT_REGION", "us-east-1")


def _build_prompt(question: str, answer: str, category: str, level: str) -> str:
    """Build the transcript-style prompt that matches the training format."""
    return "\n".join([
        "<mode:behavioral_interview>",
        f"<level:{level}>",
        f"<category:{category}>",
        "<role:interviewer>",
        question,
        "<role:candidate>",
        answer,
        "<role:interviewer_feedback>",
    ])


def _parse_feedback(raw: str) -> dict:
    """Parse structured fields from the model's raw text output."""
    result = {
        "interviewer_text": "",
        "overall": "",
        "follow_up_intent": "",
        "follow_up_question": "",
        "scores": {"situation": 0, "task": 0, "action": 0, "result": 0},
        "raw": raw,
    }
    for line in raw.splitlines():
        line = line.strip()
        if line.startswith("Interviewer reply:"):
            result["interviewer_text"] = line.replace("Interviewer reply:", "").strip()
        elif line.startswith("Overall:"):
            result["overall"] = line.replace("Overall:", "").strip()
        elif line.startswith("Follow-up intent:"):
            result["follow_up_intent"] = line.replace("Follow-up intent:", "").strip()
        elif line.startswith("Follow-up question:"):
            result["follow_up_question"] = line.replace("Follow-up question:", "").strip()
        else:
            for part in ("Situation", "Task", "Action", "Result"):
                m = re.search(rf"{part} Score:\s*(\d+)", line)
                if m:
                    result["scores"][part.lower()] = int(m.group(1))
    return result


def _call_endpoint(prompt: str) -> str:
    """Call the SageMaker endpoint and return the generated feedback."""
    # [AWS] increased read_timeout to 300s to handle cold starts and CPU inference time
    from botocore.config import Config
    config = Config(read_timeout=300, connect_timeout=30)
    runtime = boto3.client("sagemaker-runtime", region_name=REGION, config=config)
    # [AWS] 250 tokens gives the model enough room to complete the improved answer section
    payload = json.dumps({"prompt": prompt, "max_new_tokens": 250, "temperature": 0.8})
    response = runtime.invoke_endpoint(
        EndpointName=ENDPOINT_NAME,
        ContentType="application/json",
        Body=payload,
    )
    result = json.loads(response["Body"].read().decode())
    return result.get("feedback", "")


@app.route("/interview", methods=["POST"])
def interview():
    data       = request.get_json()
    session_id = data.get("session_id") or str(uuid.uuid4())
    turn_index = int(data.get("turn_index", 0))
    question   = data.get("question", "")
    answer     = data.get("answer", "")
    category   = data.get("category", "general")
    level      = data.get("level", "intern")

    prompt   = _build_prompt(question, answer, category, level)
    feedback = _call_endpoint(prompt)

    # [AWS] parse structured fields from raw model output
    parsed = _parse_feedback(feedback)

    response_payload = {
        "scores": parsed["scores"],
        "interviewer_text": parsed["interviewer_text"],
        "follow_up_question": parsed["follow_up_question"],
        "follow_up_intent": parsed["follow_up_intent"],
        "feedback": {
            "overall": parsed["overall"],
            "raw": parsed["raw"],
        },
        "confidence": 0,
    }
    save_turn(session_id, turn_index, question, answer, response_payload, question_id="", engine="nanogpt_backup")

    return jsonify({
        "session_id": session_id,
        "feedback": parsed["raw"],
        "scores": parsed["scores"],
        "interviewer_text": parsed["interviewer_text"],
        "follow_up_question": parsed["follow_up_question"],
        "follow_up_intent": parsed["follow_up_intent"],
    })


@app.route("/session/<session_id>", methods=["GET"])
def session(session_id):
    turns = get_session_turns(session_id)
    return jsonify(turns)


if __name__ == "__main__":
    app.run(debug=True, port=8000)
