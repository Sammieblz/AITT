"""
Prepare the behavioral interview dataset for GPT-style fine-tuning.

This script reads all JSONL files in this directory, validates each record,
renders transcript-style training text, tokenizes with GPT-2 BPE, and writes:

- train.bin
- val.bin
- dataset_meta.json

Unlike the char-level dataset, we intentionally do not write meta.pkl because
sampling should fall back to GPT-2 tokenization.
"""

import json
import os
import random
from typing import Iterable, List

import numpy as np
import tiktoken

# [AWS] added: load .env for AWS credentials and import boto3 for S3 upload
from dotenv import load_dotenv
import boto3
load_dotenv()

# [AWS] S3 bucket where tokenized data will be stored for SageMaker training
S3_BUCKET = os.getenv("AWS_S3_BUCKET")
S3_DATA_PREFIX = "behavioral_interview"


DATA_DIR = os.path.dirname(__file__)
END_OF_TEXT = "<|endoftext|>"
VAL_FRACTION = 0.1
RANDOM_SEED = 1337


def list_source_files() -> List[str]:
    files = []
    for name in sorted(os.listdir(DATA_DIR)):
        if not name.endswith(".jsonl"):
            continue
        if name in {"train.jsonl", "val.jsonl"}:
            continue
        files.append(os.path.join(DATA_DIR, name))
    return files


def load_examples(paths: Iterable[str]) -> List[dict]:
    examples = []
    for path in paths:
        with open(path, "r", encoding="utf-8") as f:
            for line_num, raw in enumerate(f, start=1):
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    record = json.loads(raw)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{line_num}: invalid JSON: {exc}") from exc
                validate_record(record, path, line_num)
                examples.append(record)
    if not examples:
        raise ValueError("No behavioral interview examples found. Add at least one .jsonl record.")
    return examples


def require_str(record: dict, key: str, path: str, line_num: int) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path}:{line_num}: '{key}' must be a non-empty string")
    return value.strip()


def require_list(record: dict, key: str, path: str, line_num: int) -> List[str]:
    value = record.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{path}:{line_num}: '{key}' must be a non-empty list")
    cleaned = []
    for idx, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{path}:{line_num}: '{key}[{idx}]' must be a non-empty string")
        cleaned.append(item.strip())
    return cleaned


def validate_record(record: dict, path: str, line_num: int) -> None:
    require_str(record, "id", path, line_num)
    require_str(record, "category", path, line_num)
    require_str(record, "level", path, line_num)
    require_str(record, "question", path, line_num)
    require_str(record, "candidate_answer", path, line_num)
    require_str(record, "follow_up_question", path, line_num)

    feedback = record.get("feedback")
    if not isinstance(feedback, dict):
        raise ValueError(f"{path}:{line_num}: 'feedback' must be an object")

    require_str(feedback, "overall", path, line_num)
    star = feedback.get("star")
    if not isinstance(star, dict):
        raise ValueError(f"{path}:{line_num}: 'feedback.star' must be an object")
    for part in ("situation", "task", "action", "result"):
        require_str(star, part, path, line_num)
    require_list(feedback, "strengths", path, line_num)
    require_list(feedback, "improvements", path, line_num)
    require_str(feedback, "improved_answer", path, line_num)


def render_record(record: dict) -> str:
    feedback = record["feedback"]
    star = feedback["star"]
    strengths = "\n".join(f"- {item.strip()}" for item in feedback["strengths"])
    improvements = "\n".join(f"- {item.strip()}" for item in feedback["improvements"])

    parts = [
        "<mode:behavioral_interview>",
        f"<level:{record['level'].strip()}>",
        f"<category:{record['category'].strip()}>",
        "<role:interviewer>",
        record["question"].strip(),
        "<role:candidate>",
        record["candidate_answer"].strip(),
        "<role:interviewer_feedback>",
        f"Overall: {feedback['overall'].strip()}",
        "STAR:",
        f"Situation: {star['situation'].strip()}",
        f"Task: {star['task'].strip()}",
        f"Action: {star['action'].strip()}",
        f"Result: {star['result'].strip()}",
        "Strengths:",
        strengths,
        "Improvements:",
        improvements,
        "Improved answer:",
        feedback["improved_answer"].strip(),
        "Follow-up question:",
        record["follow_up_question"].strip(),
        END_OF_TEXT,
    ]
    return "\n".join(parts)


def encode_texts(texts: List[str], enc) -> np.ndarray:
    ids: List[int] = []
    for text in texts:
        ids.extend(enc.encode(text, allowed_special={END_OF_TEXT}))
    return np.array(ids, dtype=np.uint16)


if __name__ == "__main__":
    source_files = list_source_files()
    print("Reading source files:")
    for path in source_files:
        print(f" - {os.path.basename(path)}")

    examples = load_examples(source_files)
    random.Random(RANDOM_SEED).shuffle(examples)

    split_at = max(1, int(len(examples) * (1.0 - VAL_FRACTION)))
    if split_at >= len(examples):
        split_at = len(examples) - 1

    train_examples = examples[:split_at]
    val_examples = examples[split_at:]

    train_texts = [render_record(example) for example in train_examples]
    val_texts = [render_record(example) for example in val_examples]

    enc = tiktoken.get_encoding("gpt2")
    train_ids = encode_texts(train_texts, enc)
    val_ids = encode_texts(val_texts, enc)

    train_path = os.path.join(DATA_DIR, "train.bin")
    val_path = os.path.join(DATA_DIR, "val.bin")
    train_ids.tofile(train_path)
    val_ids.tofile(val_path)

    meta = {
        "dataset": "behavioral_interview",
        "encoding": "gpt2",
        "num_examples": len(examples),
        "num_train_examples": len(train_examples),
        "num_val_examples": len(val_examples),
        "num_train_tokens": int(train_ids.size),
        "num_val_tokens": int(val_ids.size),
        "source_files": [os.path.basename(path) for path in source_files],
    }
    with open(os.path.join(DATA_DIR, "dataset_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    print(f"wrote {train_path} with {train_ids.size:,} tokens")
    print(f"wrote {val_path} with {val_ids.size:,} tokens")
    print(json.dumps(meta, indent=2))

    # [AWS] upload tokenized data and metadata to S3 so SageMaker can access them during training
    if S3_BUCKET:
        s3 = boto3.client("s3")
        uploads = [
            (train_path, f"{S3_DATA_PREFIX}/train.bin"),
            (val_path, f"{S3_DATA_PREFIX}/val.bin"),
            (os.path.join(DATA_DIR, "dataset_meta.json"), f"{S3_DATA_PREFIX}/dataset_meta.json"),
        ]
        for local_path, s3_key in uploads:
            print(f"uploading {os.path.basename(local_path)} to s3://{S3_BUCKET}/{s3_key}")
            s3.upload_file(local_path, S3_BUCKET, s3_key)
        print("S3 upload complete.")
    else:
        print("AWS_S3_BUCKET not set in .env — skipping S3 upload.")
