"""
[AWS] Interview API — calls the SageMaker endpoint and saves results to DynamoDB.

This is the backend the frontend team calls. Run locally for testing:
    python cloud-services/api.py

POST /interview
    Request:  { "session_id": "abc123", "turn_index": 1, "question": "...", "answer": "...", "category": "teamwork", "level": "intern" }
    Response: { "feedback": "Overall: ..." }

GET /session/<session_id>
    Response: [ { turn_index, question, answer, feedback, timestamp }, ... ]
"""

import os
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


def _call_endpoint(prompt: str) -> str:
    """Call the SageMaker endpoint and return the generated feedback."""
    # [AWS] increased read_timeout to 300s to handle cold starts and CPU inference time
    from botocore.config import Config
    config = Config(read_timeout=300, connect_timeout=30)
    runtime = boto3.client("sagemaker-runtime", region_name=REGION, config=config)
    payload = json.dumps({"prompt": prompt, "max_new_tokens": 100, "temperature": 0.8})
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

    # [AWS] persist the turn to DynamoDB with full structured response
    response_payload = {
        "scores": {},
        "interviewer_text": feedback,
        "follow_up_question": "",
        "follow_up_intent": "",
        "feedback": {"overall": feedback},
        "confidence": 0,
    }
    save_turn(session_id, turn_index, question, answer, response_payload, question_id=question_id, engine="nanogpt_backup")

    return jsonify({"session_id": session_id, "feedback": feedback})


@app.route("/session/<session_id>", methods=["GET"])
def session(session_id):
    turns = get_session_turns(session_id)
    return jsonify(turns)


if __name__ == "__main__":
    app.run(debug=True, port=8000)
