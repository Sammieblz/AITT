"""
[AWS] Interview API — calls the SageMaker endpoint and saves results to DynamoDB.

This is the backend the frontend team calls. Run locally for testing:
    python cloud-services/api.py

Next.js proxy routes (primary contract):
POST /session/start
    Request:  { "mode": "behavioral", "group": "...", "level": "intern", "question_id": null, "question": null }
    Response: InterviewSession shape

POST /generate-turn
    Request:  { "candidate_answer": "...", "session_id": "...", "question": "...", "group": "...", "level": "intern" }
    Response: GenerateTurnResponse shape

GET /session/<session_id>
    Response: InterviewSession shape

GET /health
    Response: { "status": "ok" }

Legacy route (kept for backwards compatibility):
POST /interview
    Request:  { "session_id": "abc123", "turn_index": 1, "question": "...", "answer": "...", "category": "teamwork", "level": "intern" }
    Response: { "session_id", "feedback", "scores", "interviewer_text", "follow_up_question", "follow_up_intent" }
"""

import os
import re
import json
import uuid
import datetime
import boto3
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from dynamodb import save_turn, get_session_turns

load_dotenv()

app = Flask(__name__)

ENDPOINT_NAME = os.getenv("SM_ENDPOINT_NAME", "aitt-behavioral-endpoint")
REGION        = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

# In-memory session store (keyed by session_id).
# Survives the process lifetime; swap for DynamoDB reads if you need persistence across restarts.
_sessions: dict = {}


def _now_iso() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"


def _make_session(session_id: str, data: dict) -> dict:
    """Build an InterviewSession-shaped dict from a /session/start request."""
    return {
        "session_id": session_id,
        "mode": data.get("mode", "behavioral"),
        "question_id": data.get("question_id"),
        "question_family_id": None,
        "group": data.get("group", ""),
        "level": data.get("level", "intern"),
        "tags": [],
        "question": data.get("question"),
        "metadata": data.get("metadata", {}),
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
        "turns": [],
    }


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
    payload = json.dumps({"prompt": prompt, "max_new_tokens": 400, "temperature": 0.8})
    response = runtime.invoke_endpoint(
        EndpointName=ENDPOINT_NAME,
        ContentType="application/json",
        Body=payload,
    )
    result = json.loads(response["Body"].read().decode())
    return result.get("feedback", "")


# --- Routes expected by the Next.js proxy ---

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/session/start", methods=["POST"])
def session_start():
    data       = request.get_json() or {}
    session_id = str(uuid.uuid4())
    session    = _make_session(session_id, data)
    _sessions[session_id] = session
    return jsonify(session)


@app.route("/generate-turn", methods=["POST"])
def generate_turn():
    data             = request.get_json() or {}
    session_id       = data.get("session_id") or str(uuid.uuid4())
    question         = data.get("question", "")
    candidate_answer = data.get("candidate_answer", "")
    group            = data.get("group", "general")
    level            = data.get("level", "intern")
    question_id      = data.get("question_id")

    prompt = _build_prompt(question, candidate_answer, group, level)
    raw    = _call_endpoint(prompt)
    parsed = _parse_feedback(raw)

    turn_index = len(_sessions.get(session_id, {}).get("turns", []))

    turn_response = {
        "engine": "nanogpt_backup",
        "session_id": session_id,
        "question_id": question_id,
        "question": question,
        "group": group,
        "tags": [],
        "candidate_answer": candidate_answer,
        "interviewer_text": parsed["interviewer_text"],
        "follow_up_question": parsed["follow_up_question"],
        "follow_up_intent": parsed["follow_up_intent"],
        "scores": parsed["scores"],
        "feedback": {
            "overall": parsed["overall"],
            "strengths": [],
            "improvements": [],
            "improved_answer": "",
            "raw": parsed["raw"],
        },
        "confidence": 0,
    }

    save_turn(session_id, turn_index, question, candidate_answer, turn_response, question_id=question_id or "", engine="nanogpt_backup")

    if session_id in _sessions:
        _sessions[session_id]["turns"].append({
            "id": turn_index,
            "turn_index": turn_index,
            "question_id": question_id,
            "question": question,
            "candidate_answer": candidate_answer,
            "engine": "nanogpt_backup",
            "prompt_version": None,
            "response": turn_response,
            "created_at": _now_iso(),
        })
        _sessions[session_id]["updated_at"] = _now_iso()

    return jsonify(turn_response)


@app.route("/session/<session_id>", methods=["GET"])
def session_get(session_id):
    if session_id in _sessions:
        return jsonify(_sessions[session_id])
    turns = get_session_turns(session_id)
    return jsonify({
        "session_id": session_id,
        "mode": "behavioral",
        "question_id": None,
        "question_family_id": None,
        "group": "",
        "level": "intern",
        "tags": [],
        "question": None,
        "metadata": {},
        "created_at": "",
        "updated_at": "",
        "turns": turns,
    })


# --- Legacy route ---

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
    parsed   = _parse_feedback(feedback)

    response_payload = {
        "scores": parsed["scores"],
        "interviewer_text": parsed["interviewer_text"],
        "follow_up_question": parsed["follow_up_question"],
        "follow_up_intent": parsed["follow_up_intent"],
        "feedback": {"overall": parsed["overall"], "raw": parsed["raw"]},
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


if __name__ == "__main__":
    app.run(debug=True, port=8000)
