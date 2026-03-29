"""
Prepare the behavioral interview dataset for retrieval and nanoGPT fine-tuning.

This script normalizes both the hand-authored seed data and the generated
question-family corpus into one canonical schema, splits by question family to
avoid train/validation leakage, writes retrieval-ready JSON artifacts, and
emits GPT-2-tokenized `train.bin` and `val.bin`.
"""

from __future__ import annotations

import json
import os
import random
import re
from collections import Counter, defaultdict
from typing import Iterable, List

import numpy as np
import tiktoken


DATA_DIR = os.path.dirname(__file__)
END_OF_TEXT = "<|endoftext|>"
VAL_FRACTION = 0.15
RANDOM_SEED = 1337
SOURCE_JSON_SUFFIX = ".source.json"
NORMALIZED_EXAMPLES_FILE = "normalized_examples.json"
EVAL_EXAMPLES_FILE = "eval_examples.json"

CANONICAL_GROUPS = (
    "Leadership & Influence",
    "Conflict & Collaboration",
    "Problem Solving & Technical Judgment",
    "Failure & Resilience",
    "Achievement & Impact",
    "Adaptability & Growth",
)
GROUP_TAGS = {
    "Leadership & Influence": ["leadership", "influence", "ownership"],
    "Conflict & Collaboration": ["collaboration", "communication", "conflict"],
    "Problem Solving & Technical Judgment": ["problem-solving", "technical-judgment", "tradeoffs"],
    "Failure & Resilience": ["resilience", "reflection", "accountability"],
    "Achievement & Impact": ["impact", "execution", "delivery"],
    "Adaptability & Growth": ["adaptability", "learning", "growth"],
}
LEGACY_GROUP_MAP = {
    "ownership": "Leadership & Influence",
    "leadership": "Leadership & Influence",
    "teamwork": "Conflict & Collaboration",
    "feedback": "Failure & Resilience",
    "accountability": "Failure & Resilience",
    "ambiguity": "Problem Solving & Technical Judgment",
    "prioritization": "Achievement & Impact",
    "learning": "Adaptability & Growth",
    "adaptability": "Adaptability & Growth",
}
VALID_LEVELS = {"intern", "new_grad"}
VALID_ANSWER_PROFILES = {
    "strong",
    "adequate",
    "weak",
    "missing_result",
    "we_language",
    "rambling",
    "no_example",
    "emotional",
    "short",
    "unspecified",
}
VALID_RATINGS = {"strong", "good", "weak", "missing"}
STAR_PARTS = ("situation", "task", "action", "result")
RATING_TO_SCORE = {"strong": 5, "good": 4, "weak": 2, "missing": 1}
SCORE_TO_RATING = {
    5: "strong",
    4: "good",
    3: "good",
    2: "weak",
    1: "missing",
}
QUALITY_TO_PROFILE = {
    "strong": "strong",
    "weak": "weak",
    "mixed": "adequate",
    "unspecified": "unspecified",
}


def _ensure_generated_assets() -> None:
    try:
        from build_assets import build_assets  # type: ignore
    except Exception:
        return
    build_assets()


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def list_source_files() -> List[str]:
    files = []
    for name in sorted(os.listdir(DATA_DIR)):
        if name.endswith(".jsonl") or name.endswith(SOURCE_JSON_SUFFIX):
            files.append(os.path.join(DATA_DIR, name))
    return files


def require_str(record: dict, key: str, path: str, line_num: int) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{path}:{line_num}: '{key}' must be a non-empty string")
    return value.strip()


def require_optional_str(record: dict, key: str) -> str | None:
    value = record.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        return None
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


def normalize_group(record: dict, path: str, line_num: int) -> str:
    raw_group = require_optional_str(record, "group") or require_optional_str(record, "category")
    if raw_group is None:
        raise ValueError(f"{path}:{line_num}: record must include 'group' or 'category'")
    canonical = LEGACY_GROUP_MAP.get(raw_group, raw_group)
    if canonical not in CANONICAL_GROUPS:
        raise ValueError(f"{path}:{line_num}: unknown canonical group '{canonical}'")
    return canonical


def normalize_level(record: dict, path: str, line_num: int) -> str:
    level = require_str(record, "level", path, line_num)
    if level not in VALID_LEVELS:
        raise ValueError(f"{path}:{line_num}: level must be one of {sorted(VALID_LEVELS)}")
    return level


def normalize_tags(record: dict, group: str, path: str, line_num: int) -> list[str]:
    raw_tags = record.get("tags")
    tags: list[str] = []
    if raw_tags is not None:
        if not isinstance(raw_tags, list):
            raise ValueError(f"{path}:{line_num}: 'tags' must be a list when present")
        for idx, item in enumerate(raw_tags):
            if not isinstance(item, str) or not item.strip():
                raise ValueError(f"{path}:{line_num}: tags[{idx}] must be a non-empty string")
            tags.append(item.strip())
    else:
        legacy_category = require_optional_str(record, "category")
        if legacy_category and legacy_category not in CANONICAL_GROUPS:
            tags.append(slugify(legacy_category))
    tags = [*GROUP_TAGS[group], *tags]
    return list(dict.fromkeys(tags))


def normalize_answer_profile(base: dict, variant: dict | None) -> tuple[str, str]:
    candidate = (
        require_optional_str(variant or {}, "answer_profile")
        or require_optional_str(variant or {}, "quality")
        or require_optional_str(base, "answer_profile")
        or require_optional_str(base, "quality")
        or "unspecified"
    )
    profile = QUALITY_TO_PROFILE.get(candidate, candidate)
    if profile not in VALID_ANSWER_PROFILES:
        profile = "unspecified"
    quality = require_optional_str(variant or {}, "quality") or require_optional_str(base, "quality") or profile
    return profile, quality


def normalize_star_entry(entry: object, part: str, path: str, line_num: int) -> dict:
    if isinstance(entry, str):
        return {"score": 4, "rating": "good", "feedback": entry.strip()}
    if not isinstance(entry, dict):
        raise ValueError(f"{path}:{line_num}: STAR entry '{part}' must be a string or object")

    raw_feedback = entry.get("feedback")
    if not isinstance(raw_feedback, str) or not raw_feedback.strip():
        raise ValueError(f"{path}:{line_num}: STAR entry '{part}.feedback' must be a non-empty string")

    raw_score = entry.get("score")
    raw_rating = entry.get("rating")
    score: int | None = None
    rating: str | None = None

    if isinstance(raw_score, int):
        score = min(5, max(1, raw_score))
        rating = SCORE_TO_RATING[score]
    elif isinstance(raw_score, float):
        score = min(5, max(1, round(raw_score)))
        rating = SCORE_TO_RATING[score]

    if isinstance(raw_rating, str) and raw_rating.strip() in VALID_RATINGS:
        rating = raw_rating.strip()
        score = score or RATING_TO_SCORE[rating]

    if rating is None or score is None:
        raise ValueError(
            f"{path}:{line_num}: STAR entry '{part}' must define 'score' (1-5) or rating in {sorted(VALID_RATINGS)}"
        )

    return {
        "score": score,
        "rating": rating,
        "feedback": raw_feedback.strip(),
    }


def normalize_feedback(feedback: dict, path: str, line_num: int) -> dict:
    if not isinstance(feedback, dict):
        raise ValueError(f"{path}:{line_num}: 'feedback' must be an object")

    overall = require_str(feedback, "overall", path, line_num)
    strengths = require_list(feedback, "strengths", path, line_num)
    improvements = require_list(feedback, "improvements", path, line_num)
    improved_answer = require_str(feedback, "improved_answer", path, line_num)
    interviewer_reply = require_optional_str(feedback, "interviewer_reply") or overall
    follow_up_intent = require_optional_str(feedback, "follow_up_intent") or ""

    star = feedback.get("star")
    if not isinstance(star, dict):
        raise ValueError(f"{path}:{line_num}: 'feedback.star' must be an object")

    normalized_star = {}
    for part in STAR_PARTS:
        normalized_star[part] = normalize_star_entry(star.get(part), part, path, line_num)

    return {
        "interviewer_reply": interviewer_reply,
        "overall": overall,
        "follow_up_intent": follow_up_intent,
        "star": normalized_star,
        "strengths": strengths,
        "improvements": improvements,
        "improved_answer": improved_answer,
    }


def derive_follow_up_intent(feedback: dict) -> str:
    intent = feedback.get("follow_up_intent")
    if isinstance(intent, str) and intent.strip():
        return intent.strip()
    weakest = min(
        STAR_PARTS,
        key=lambda part: feedback["star"][part]["score"],
    )
    return {
        "situation": "clarify_situation",
        "task": "clarify_task",
        "action": "clarify_action",
        "result": "clarify_result",
    }[weakest]


def normalize_example(base: dict, variant: dict | None, path: str, line_num: int) -> dict:
    group = normalize_group(base, path, line_num)
    level = normalize_level(base, path, line_num)
    question = require_str(base, "question", path, line_num)
    tags = normalize_tags(base, group, path, line_num)
    question_id = require_optional_str(base, "question_id") or slugify(question)
    question_family_id = require_optional_str(base, "question_family_id") or f"{question_id}--{level}"
    source_kind = require_optional_str(base, "source_kind") or ("legacy_seed" if base.get("source_url") else "authored_seed")
    answer_profile, quality = normalize_answer_profile(base, variant)

    container = variant if variant is not None else base
    feedback = normalize_feedback(container.get("feedback"), path, line_num)
    follow_up_question = require_str(container, "follow_up_question", path, line_num)
    source_id = require_optional_str(base, "id") or question_family_id
    example_id = (
        require_optional_str(container, "id")
        or f"{question_family_id}--{answer_profile}"
    )

    return {
        "id": example_id,
        "record_id": source_id,
        "question_id": question_id,
        "question_family_id": question_family_id,
        "group": group,
        "category": group,
        "tags": tags,
        "level": level,
        "answer_profile": answer_profile,
        "quality": quality,
        "source_kind": source_kind,
        "source_url": require_optional_str(base, "source_url") or "",
        "question": question,
        "candidate_answer": require_str(container, "candidate_answer", path, line_num),
        "follow_up_question": follow_up_question,
        "feedback": {
            **feedback,
            "follow_up_intent": derive_follow_up_intent(feedback),
        },
    }


def append_record_examples(examples: List[dict], record: dict, path: str, line_num: int) -> None:
    normalize_group(record, path, line_num)
    normalize_level(record, path, line_num)
    require_str(record, "question", path, line_num)

    variants = record.get("variants")
    if variants is None:
        examples.append(normalize_example(record, None, path, line_num))
        return

    if not isinstance(variants, list) or not variants:
        raise ValueError(f"{path}:{line_num}: 'variants' must be a non-empty list")
    for idx, variant in enumerate(variants):
        if not isinstance(variant, dict):
            raise ValueError(f"{path}:{line_num}: variants[{idx}] must be an object")
        examples.append(normalize_example(record, variant, path, line_num))


def load_examples(paths: Iterable[str]) -> List[dict]:
    examples = []
    for path in paths:
        if path.endswith(".jsonl"):
            with open(path, "r", encoding="utf-8") as f:
                for line_num, raw in enumerate(f, start=1):
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        record = json.loads(raw)
                    except json.JSONDecodeError as exc:
                        raise ValueError(f"{path}:{line_num}: invalid JSON: {exc}") from exc
                    append_record_examples(examples, record, path, line_num)
            continue

        with open(path, "r", encoding="utf-8") as f:
            try:
                payload = json.load(f)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}: invalid JSON: {exc}") from exc

        records = payload if isinstance(payload, list) else [payload]
        if not records:
            raise ValueError(f"{path}: source file must contain at least one record")
        for record_index, record in enumerate(records, start=1):
            if not isinstance(record, dict):
                raise ValueError(f"{path}: record {record_index} must be an object")
            append_record_examples(examples, record, path, record_index)

    if not examples:
        raise ValueError(
            "No behavioral interview examples found. Add at least one .jsonl or .source.json record."
        )
    return examples


def render_full_feedback(record: dict) -> str:
    feedback = record["feedback"]
    star = feedback["star"]
    strengths = "\n".join(f"- {item}" for item in feedback["strengths"])
    improvements = "\n".join(f"- {item}" for item in feedback["improvements"])

    parts = [
        "<mode:behavioral_interview>",
        "<task:full_feedback>",
        f"<level:{record['level']}>",
        f"<group:{record['group']}>",
        f"<question_id:{record['question_id']}>",
        f"<question_family_id:{record['question_family_id']}>",
        f"<answer_profile:{record['answer_profile']}>",
        f"<tags:{', '.join(record['tags'])}>",
        "<role:interviewer>",
        f"Question: {record['question']}",
        "<role:candidate>",
        record["candidate_answer"],
        "<role:interviewer_feedback>",
        f"Interviewer reply: {feedback['interviewer_reply']}",
        f"Overall: {feedback['overall']}",
        f"Follow-up intent: {feedback['follow_up_intent']}",
        "STAR:",
        f"Situation Score: {star['situation']['score']}",
        f"Situation Rating: {star['situation']['rating']}",
        f"Situation Feedback: {star['situation']['feedback']}",
        f"Task Score: {star['task']['score']}",
        f"Task Rating: {star['task']['rating']}",
        f"Task Feedback: {star['task']['feedback']}",
        f"Action Score: {star['action']['score']}",
        f"Action Rating: {star['action']['rating']}",
        f"Action Feedback: {star['action']['feedback']}",
        f"Result Score: {star['result']['score']}",
        f"Result Rating: {star['result']['rating']}",
        f"Result Feedback: {star['result']['feedback']}",
        "Strengths:",
        strengths,
        "Improvements:",
        improvements,
        "Improved answer:",
        feedback["improved_answer"],
        "Follow-up question:",
        record["follow_up_question"],
        END_OF_TEXT,
    ]
    return "\n".join(parts)


def render_reply_only(record: dict) -> str:
    feedback = record["feedback"]
    star = feedback["star"]
    parts = [
        "<mode:behavioral_interview>",
        "<task:reply_only>",
        f"<level:{record['level']}>",
        f"<group:{record['group']}>",
        f"<question_id:{record['question_id']}>",
        f"<question_family_id:{record['question_family_id']}>",
        f"<answer_profile:{record['answer_profile']}>",
        "<role:interviewer>",
        f"Question: {record['question']}",
        "<role:candidate>",
        record["candidate_answer"],
        "<role:interviewer_feedback>",
        f"Interviewer reply: {feedback['interviewer_reply']}",
        f"Overall: {feedback['overall']}",
        f"Follow-up intent: {feedback['follow_up_intent']}",
        f"Situation Score: {star['situation']['score']}",
        f"Task Score: {star['task']['score']}",
        f"Action Score: {star['action']['score']}",
        f"Result Score: {star['result']['score']}",
        "Follow-up question:",
        record["follow_up_question"],
        END_OF_TEXT,
    ]
    return "\n".join(parts)


def render_improved_answer(record: dict) -> str:
    feedback = record["feedback"]
    parts = [
        "<mode:behavioral_interview>",
        "<task:improve_answer>",
        f"<level:{record['level']}>",
        f"<group:{record['group']}>",
        f"<question_id:{record['question_id']}>",
        f"<question_family_id:{record['question_family_id']}>",
        f"<answer_profile:{record['answer_profile']}>",
        "<role:interviewer>",
        f"Question: {record['question']}",
        "<role:candidate>",
        record["candidate_answer"],
        "<role:interviewer_feedback>",
        f"Interviewer reply: {feedback['interviewer_reply']}",
        "Improvements:",
        "\n".join(f"- {item}" for item in feedback["improvements"]),
        "Improved answer:",
        feedback["improved_answer"],
        "Follow-up question:",
        record["follow_up_question"],
        END_OF_TEXT,
    ]
    return "\n".join(parts)


def render_record_variants(record: dict) -> List[str]:
    return [
        render_full_feedback(record),
        render_reply_only(record),
        render_improved_answer(record),
    ]


def encode_texts(texts: List[str], enc) -> np.ndarray:
    ids: List[int] = []
    for text in texts:
        ids.extend(enc.encode(text, allowed_special={END_OF_TEXT}))
    return np.array(ids, dtype=np.uint16)


def validate_examples(examples: list[dict]) -> None:
    if not examples:
        raise ValueError("Expected at least one normalized example")

    seen_ids: set[str] = set()
    question_to_group: dict[str, str] = {}
    for example in examples:
        example_id = example["id"]
        if example_id in seen_ids:
            raise ValueError(f"Duplicate example id detected: {example_id}")
        seen_ids.add(example_id)

        group = example["group"]
        if group not in CANONICAL_GROUPS:
            raise ValueError(f"Invalid canonical group in example {example_id}: {group}")
        if example["level"] not in VALID_LEVELS:
            raise ValueError(f"Invalid level in example {example_id}: {example['level']}")
        if example["answer_profile"] not in VALID_ANSWER_PROFILES:
            raise ValueError(f"Invalid answer_profile in example {example_id}: {example['answer_profile']}")
        if not example["tags"]:
            raise ValueError(f"Example {example_id} is missing tags")

        question_id = example["question_id"]
        previous_group = question_to_group.get(question_id)
        if previous_group is not None and previous_group != group:
            raise ValueError(f"Question {question_id} appears in multiple groups: {previous_group} vs {group}")
        question_to_group[question_id] = group

        for part in STAR_PARTS:
            payload = example["feedback"]["star"][part]
            if payload["score"] not in {1, 2, 3, 4, 5}:
                raise ValueError(f"Example {example_id} has invalid score for {part}: {payload['score']}")
            if payload["rating"] not in VALID_RATINGS:
                raise ValueError(f"Example {example_id} has invalid rating for {part}: {payload['rating']}")
        if not example["feedback"]["follow_up_intent"]:
            raise ValueError(f"Example {example_id} is missing follow_up_intent")


def split_examples_by_family(examples: list[dict]) -> tuple[list[dict], list[dict], list[str], list[str]]:
    families: dict[str, list[dict]] = defaultdict(list)
    for example in examples:
        families[example["question_family_id"]].append(example)

    family_ids = sorted(families)
    rng = random.Random(RANDOM_SEED)
    rng.shuffle(family_ids)

    train_family_count = max(1, int(len(family_ids) * (1.0 - VAL_FRACTION)))
    if train_family_count >= len(family_ids):
        train_family_count = len(family_ids) - 1
    if train_family_count <= 0:
        raise ValueError("Need at least two question families to create train/validation split")

    train_family_ids = sorted(family_ids[:train_family_count])
    val_family_ids = sorted(family_ids[train_family_count:])

    overlap = set(train_family_ids) & set(val_family_ids)
    if overlap:
        raise ValueError(f"Question family leakage detected in split: {sorted(overlap)}")

    train_examples = [example for family_id in train_family_ids for example in families[family_id]]
    val_examples = [example for family_id in val_family_ids for example in families[family_id]]
    return train_examples, val_examples, train_family_ids, val_family_ids


def build_meta(
    source_files: list[str],
    examples: list[dict],
    train_examples: list[dict],
    val_examples: list[dict],
    train_texts: list[str],
    val_texts: list[str],
    train_ids: np.ndarray,
    val_ids: np.ndarray,
    train_family_ids: list[str],
    val_family_ids: list[str],
) -> dict:
    groups = Counter(example["group"] for example in examples)
    answer_profiles = Counter(example["answer_profile"] for example in examples)
    levels = Counter(example["level"] for example in examples)
    return {
        "dataset": "behavioral_interview",
        "encoding": "gpt2",
        "num_examples": len(examples),
        "num_question_families": len({example["question_family_id"] for example in examples}),
        "num_train_examples": len(train_examples),
        "num_val_examples": len(val_examples),
        "num_train_sequences": len(train_texts),
        "num_val_sequences": len(val_texts),
        "num_train_tokens": int(train_ids.size),
        "num_val_tokens": int(val_ids.size),
        "train_question_family_ids": train_family_ids,
        "val_question_family_ids": val_family_ids,
        "train_question_family_overlap": len(set(train_family_ids) & set(val_family_ids)),
        "groups": dict(groups),
        "answer_profiles": dict(answer_profiles),
        "levels": dict(levels),
        "source_files": [os.path.basename(path) for path in source_files],
    }


def prepare_dataset() -> dict:
    _ensure_generated_assets()
    source_files = list_source_files()
    examples = load_examples(source_files)
    validate_examples(examples)

    examples = sorted(
        examples,
        key=lambda item: (
            item["group"],
            item["level"],
            item["question_family_id"],
            item["answer_profile"],
            item["id"],
        ),
    )

    train_examples, val_examples, train_family_ids, val_family_ids = split_examples_by_family(examples)

    train_texts = [text for example in train_examples for text in render_record_variants(example)]
    val_texts = [text for example in val_examples for text in render_record_variants(example)]

    enc = tiktoken.get_encoding("gpt2")
    train_ids = encode_texts(train_texts, enc)
    val_ids = encode_texts(val_texts, enc)

    train_path = os.path.join(DATA_DIR, "train.bin")
    val_path = os.path.join(DATA_DIR, "val.bin")
    train_ids.tofile(train_path)
    val_ids.tofile(val_path)

    meta = build_meta(
        source_files=source_files,
        examples=examples,
        train_examples=train_examples,
        val_examples=val_examples,
        train_texts=train_texts,
        val_texts=val_texts,
        train_ids=train_ids,
        val_ids=val_ids,
        train_family_ids=train_family_ids,
        val_family_ids=val_family_ids,
    )

    with open(os.path.join(DATA_DIR, "dataset_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)
    with open(os.path.join(DATA_DIR, NORMALIZED_EXAMPLES_FILE), "w", encoding="utf-8") as f:
        json.dump(examples, f, indent=2)
    with open(os.path.join(DATA_DIR, EVAL_EXAMPLES_FILE), "w", encoding="utf-8") as f:
        json.dump(val_examples, f, indent=2)

    return meta


if __name__ == "__main__":
    meta = prepare_dataset()
    print(f"wrote {os.path.join(DATA_DIR, 'train.bin')} with {meta['num_train_tokens']:,} tokens")
    print(f"wrote {os.path.join(DATA_DIR, 'val.bin')} with {meta['num_val_tokens']:,} tokens")
    print(f"wrote {NORMALIZED_EXAMPLES_FILE} with {meta['num_examples']} normalized examples")
    print(f"wrote {EVAL_EXAMPLES_FILE} with {meta['num_val_examples']} validation examples")
    print(json.dumps(meta, indent=2))
