"""
[AWS] DynamoDB helpers for storing interview session data.

Table schema:
    session_id  (PK, string)  — unique interview session
    turn_index  (SK, number)  — turn number within the session
    timestamp   (string)      — ISO timestamp
    question    (string)      — interviewer question
    answer      (string)      — candidate's answer
    feedback    (string)      — STAR feedback from the model
    category    (string)      — e.g. "teamwork", "adaptability"
    level       (string)      — e.g. "intern", "new_grad"

Usage:
    from cloud-services.dynamodb import save_turn, get_session
"""

import os
import boto3
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

TABLE_NAME = os.getenv("DYNAMODB_TABLE", "aitt-sessions")

def _get_table():
    dynamodb = boto3.resource("dynamodb", region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
    return dynamodb.Table(TABLE_NAME)


def save_turn(session_id: str, turn_index: int, question: str, answer: str, feedback: str, category: str = "", level: str = "") -> dict:
    """Save a single interview turn to DynamoDB."""
    table = _get_table()
    item = {
        "session_id": session_id,
        "turn_index": turn_index,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "answer": answer,
        "feedback": feedback,
        "category": category,
        "level": level,
    }
    table.put_item(Item=item)
    return item


def get_session(session_id: str) -> list:
    """Retrieve all turns for a session, ordered by turn_index."""
    table = _get_table()
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("session_id").eq(session_id)
    )
    items = response.get("Items", [])
    return sorted(items, key=lambda x: int(x["turn_index"]))


def create_table_if_not_exists():
    """[AWS] One-time setup — create the DynamoDB table if it doesn't exist."""
    dynamodb = boto3.resource("dynamodb", region_name=os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
    existing = [t.name for t in dynamodb.tables.all()]
    if TABLE_NAME in existing:
        print(f"Table '{TABLE_NAME}' already exists.")
        return

    table = dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[
            {"AttributeName": "session_id", "KeyType": "HASH"},
            {"AttributeName": "turn_index", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "session_id", "AttributeType": "S"},
            {"AttributeName": "turn_index", "AttributeType": "N"},
        ],
        BillingMode="PAY_PER_REQUEST",  # [AWS] on-demand pricing, no capacity planning needed
    )
    table.wait_until_exists()
    print(f"Table '{TABLE_NAME}' created.")


if __name__ == "__main__":
    create_table_if_not_exists()
