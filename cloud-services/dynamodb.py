"""
[AWS] DynamoDB helpers for storing interview session data.

Tables:
    aitt-sessions   — session metadata (mirrors interview_sessions in SQLite)
    aitt-turns      — per-turn data with structured STAR scores (mirrors interview_turns)
    aitt-content    — question bank and normalized examples (mirrors question_bank + normalized_examples)

Session table schema:
    session_id          (PK, string)
    mode                (string)  — e.g. "behavioral"
    question_id         (string)
    question_family_id  (string)
    group               (string)  — e.g. "Conflict & Collaboration"
    level               (string)  — e.g. "intern", "new_grad"
    tags                (list)
    question            (string)
    metadata            (map)
    created_at          (string)
    updated_at          (string)

Turns table schema:
    session_id      (PK, string)
    turn_index      (SK, number)
    question_id     (string)
    question        (string)
    candidate_answer(string)
    engine          (string)      — which model generated the response
    prompt_version  (string)
    scores          (map)         — { situation, task, action, result } 1-5
    interviewer_text(string)
    follow_up_question (string)
    follow_up_intent   (string)
    feedback        (map)         — { overall, strengths, improvements, improved_answer }
    confidence      (number)
    response_json   (string)      — full raw response JSON for debugging
    created_at      (string)

Content table schema:
    content_type    (PK, string)  — "question" or "example"
    content_id      (SK, string)  — question_id or example_id
    group           (string)
    tags            (list)
    level           (string)      — examples only
    answer_profile  (string)      — examples only
    question        (string)
    data_json       (string)      — full record JSON
    updated_at      (string)
"""

import json
import os
import boto3
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

SESSIONS_TABLE = os.getenv("DYNAMODB_SESSIONS_TABLE", "aitt-sessions")
TURNS_TABLE    = os.getenv("DYNAMODB_TURNS_TABLE", "aitt-turns")
CONTENT_TABLE  = os.getenv("DYNAMODB_CONTENT_TABLE", "aitt-content")
REGION         = os.getenv("AWS_DEFAULT_REGION", "us-east-1")


def _get_resource():
    return boto3.resource("dynamodb", region_name=REGION)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ── Session helpers ────────────────────────────────────────────────────────────

def create_session(
    session_id: str,
    mode: str = "behavioral",
    group: str = "",
    level: str = "intern",
    question_id: str = "",
    question_family_id: str = "",
    question: str = "",
    tags: list = None,
    metadata: dict = None,
) -> dict:
    """Create a new interview session."""
    table = _get_resource().Table(SESSIONS_TABLE)
    now = _utc_now()
    item = {
        "session_id": session_id,
        "mode": mode,
        "group": group,
        "level": level,
        "question_id": question_id,
        "question_family_id": question_family_id,
        "question": question,
        "tags": tags or [],
        "metadata": metadata or {},
        "created_at": now,
        "updated_at": now,
    }
    table.put_item(Item=item)
    return item


def get_session(session_id: str) -> dict:
    """Retrieve a session by ID."""
    table = _get_resource().Table(SESSIONS_TABLE)
    response = table.get_item(Key={"session_id": session_id})
    return response.get("Item")


def update_session(session_id: str, **kwargs) -> None:
    """Update session fields."""
    table = _get_resource().Table(SESSIONS_TABLE)
    kwargs["updated_at"] = _utc_now()
    expr = "SET " + ", ".join(f"#{k} = :{k}" for k in kwargs)
    names = {f"#{k}": k for k in kwargs}
    values = {f":{k}": v for k, v in kwargs.items()}
    table.update_item(
        Key={"session_id": session_id},
        UpdateExpression=expr,
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
    )


# ── Turn helpers ───────────────────────────────────────────────────────────────

def save_turn(
    session_id: str,
    turn_index: int,
    question: str,
    candidate_answer: str,
    response: dict,
    question_id: str = "",
    engine: str = "unknown",
    prompt_version: str = "",
) -> dict:
    """Save a single interview turn with full structured response."""
    table = _get_resource().Table(TURNS_TABLE)
    item = {
        "session_id": session_id,
        "turn_index": turn_index,
        "question_id": question_id,
        "question": question,
        "candidate_answer": candidate_answer,
        "engine": engine,
        "prompt_version": prompt_version,
        "scores": response.get("scores", {}),
        "interviewer_text": response.get("interviewer_text", ""),
        "follow_up_question": response.get("follow_up_question", ""),
        "follow_up_intent": response.get("follow_up_intent", ""),
        "feedback": response.get("feedback", {}),
        "confidence": str(response.get("confidence", 0)),  # DynamoDB requires Decimal for float
        "response_json": json.dumps(response),
        "created_at": _utc_now(),
    }
    table.put_item(Item=item)
    return item


def get_session_turns(session_id: str) -> list:
    """Retrieve all turns for a session ordered by turn_index."""
    table = _get_resource().Table(TURNS_TABLE)
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("session_id").eq(session_id)
    )
    items = response.get("Items", [])
    return sorted(items, key=lambda x: int(x["turn_index"]))


# ── Content helpers ────────────────────────────────────────────────────────────

def upsert_question(question: dict) -> None:
    """Store a question from the question bank."""
    table = _get_resource().Table(CONTENT_TABLE)
    table.put_item(Item={
        "content_type": "question",
        "content_id": question["question_id"],
        "group": question.get("group", ""),
        "tags": question.get("tags", []),
        "question": question.get("question", ""),
        "data_json": json.dumps(question),
        "updated_at": _utc_now(),
    })


def upsert_example(example: dict) -> None:
    """Store a normalized training example."""
    table = _get_resource().Table(CONTENT_TABLE)
    table.put_item(Item={
        "content_type": "example",
        "content_id": example["id"],
        "group": example.get("group", ""),
        "tags": example.get("tags", []),
        "level": example.get("level", ""),
        "answer_profile": example.get("answer_profile", ""),
        "question": example.get("question", ""),
        "data_json": json.dumps(example),
        "updated_at": _utc_now(),
    })


def get_question(question_id: str) -> dict:
    """Retrieve a question by ID."""
    table = _get_resource().Table(CONTENT_TABLE)
    response = table.get_item(Key={"content_type": "question", "content_id": question_id})
    item = response.get("Item")
    if item:
        return json.loads(item["data_json"])
    return None


# ── Table setup ────────────────────────────────────────────────────────────────

def create_tables_if_not_exist() -> None:
    """[AWS] One-time setup — create all DynamoDB tables if they don't exist."""
    dynamodb = _get_resource()
    existing = {t.name for t in dynamodb.tables.all()}

    tables_to_create = [
        {
            "TableName": SESSIONS_TABLE,
            "KeySchema": [{"AttributeName": "session_id", "KeyType": "HASH"}],
            "AttributeDefinitions": [{"AttributeName": "session_id", "AttributeType": "S"}],
        },
        {
            "TableName": TURNS_TABLE,
            "KeySchema": [
                {"AttributeName": "session_id", "KeyType": "HASH"},
                {"AttributeName": "turn_index", "KeyType": "RANGE"},
            ],
            "AttributeDefinitions": [
                {"AttributeName": "session_id", "AttributeType": "S"},
                {"AttributeName": "turn_index", "AttributeType": "N"},
            ],
        },
        {
            "TableName": CONTENT_TABLE,
            "KeySchema": [
                {"AttributeName": "content_type", "KeyType": "HASH"},
                {"AttributeName": "content_id", "KeyType": "RANGE"},
            ],
            "AttributeDefinitions": [
                {"AttributeName": "content_type", "AttributeType": "S"},
                {"AttributeName": "content_id", "AttributeType": "S"},
            ],
        },
    ]

    for spec in tables_to_create:
        name = spec["TableName"]
        if name in existing:
            print(f"Table '{name}' already exists.")
            continue
        table = dynamodb.create_table(
            **spec,
            BillingMode="PAY_PER_REQUEST",
        )
        table.wait_until_exists()
        print(f"Table '{name}' created.")


if __name__ == "__main__":
    create_tables_if_not_exist()
