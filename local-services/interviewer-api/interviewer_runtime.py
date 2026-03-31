from __future__ import annotations

import argparse
import json
import os
import re
import time
from contextlib import nullcontext
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib import request

import torch
import tiktoken

from local_model.model import GPT, GPTConfig


SERVICE_DIR = Path(__file__).resolve().parent
REPO_ROOT = SERVICE_DIR.parents[1]
LOCAL_MODEL_DIR = REPO_ROOT / "local_model"
DATASET_DIR = Path(
    os.getenv("AITT_BEHAVIORAL_DATA_DIR", str(LOCAL_MODEL_DIR / "data" / "behavioral_interview"))
).resolve()
END_OF_TEXT = "<|endoftext|>"
STAR_PARTS = ("situation", "task", "action", "result")
VALID_INTENTS = {
    "clarify_situation",
    "clarify_task",
    "clarify_action",
    "clarify_result",
    "reduce_we_language",
    "tighten_rambling",
    "reframe_no_example",
    "support_emotional",
    "praise_strong",
}
VALID_ENGINES = ("local_primary", "nanogpt_backup", "heuristic_dev")
DEFAULT_EXAMPLES_PATH = str(DATASET_DIR / "normalized_examples.json")
DEFAULT_HANDOFF_PATH = str(DATASET_DIR / "researcher_handoff.md")
DEFAULT_CHECKPOINT_PATH = str(LOCAL_MODEL_DIR / "out-behavioral" / "ckpt.pt")
SMOKE_CHECKPOINT_PATH = str(LOCAL_MODEL_DIR / "out-behavioral-smoke" / "ckpt.pt")
DEFAULT_OLLAMA_MODEL = os.getenv("AITT_OLLAMA_MODEL", "qwen2.5:1.5b-instruct-q4_0")
DEFAULT_OLLAMA_BASE_URL = os.getenv("AITT_OLLAMA_BASE_URL", "http://127.0.0.1:11434")
PROMPT_VERSION = "behavioral_json_v2"
FOLLOW_UP_BY_INTENT = {
    "clarify_situation": "Can you tighten the context and explain the core challenge in one or two sentences?",
    "clarify_task": "What exactly were you personally responsible for in that situation?",
    "clarify_action": "What did you personally do that changed the direction of the situation?",
    "clarify_result": "What happened because of your actions, and can you quantify it if possible?",
    "reduce_we_language": "I want to hear your individual contribution. Which part did you personally own?",
    "tighten_rambling": "Let's tighten the setup. What was the core challenge, and what did you do about it?",
    "reframe_no_example": "A class project, hackathon, club, internship, or research project can all work. Which related example comes closest?",
    "support_emotional": "That sounds difficult. How would you summarize how you responded and what you learned in a professional interview setting?",
    "praise_strong": "Strong answer. If you wanted to make it even sharper, what metric or reflection would you add?",
}
RATING_TO_SCORE = {"strong": 5, "good": 4, "weak": 2, "missing": 1}
SCORE_TO_RATING = {5: "strong", 4: "good", 3: "good", 2: "weak", 1: "missing"}
OLLAMA_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "interviewer_text": {"type": "string"},
        "follow_up_question": {"type": "string"},
        "follow_up_intent": {"type": "string", "enum": sorted(VALID_INTENTS)},
        "scores": {
            "type": "object",
            "properties": {part: {"type": "integer", "minimum": 1, "maximum": 5} for part in STAR_PARTS},
            "required": list(STAR_PARTS),
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": [
        "interviewer_text",
        "follow_up_question",
        "follow_up_intent",
        "scores",
        "confidence",
    ],
}


def _default_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


def _default_dtype(device: str) -> str:
    if device.startswith("cuda") and torch.cuda.is_bf16_supported():
        return "bfloat16"
    if device.startswith("cuda"):
        return "float16"
    return "float32"


def _resolve_engine_order(primary_engine: str | None, available_engines: list[str] | None = None) -> list[str]:
    requested = [engine for engine in (available_engines or list(VALID_ENGINES)) if engine in VALID_ENGINES]
    seen: set[str] = set()
    ordered: list[str] = []
    primary = primary_engine if primary_engine in VALID_ENGINES else None
    if primary is not None:
        ordered.append(primary)
        seen.add(primary)
    for engine in requested:
        if engine not in seen:
            ordered.append(engine)
            seen.add(engine)
    for engine in VALID_ENGINES:
        if engine not in seen:
            ordered.append(engine)
    return ordered


def _normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _load_examples(path: str) -> list[dict[str, Any]]:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, list):
        raise ValueError(f"{path} must contain a JSON list of normalized examples")
    return payload


def _load_rules(path: str) -> str:
    if not os.path.exists(path):
        return ""
    return Path(path).read_text(encoding="utf-8").strip()


def _score_to_rating(score: int) -> str:
    score = max(1, min(5, int(score)))
    return SCORE_TO_RATING[score]


def _coerce_score(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return max(1, min(5, int(round(value))))
    if isinstance(value, str):
        cleaned = value.strip().lower()
        if cleaned.isdigit():
            return max(1, min(5, int(cleaned)))
        if cleaned in RATING_TO_SCORE:
            return RATING_TO_SCORE[cleaned]
    return None


def _extract_json_candidate(text: str) -> str | None:
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        return stripped
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return stripped[start : end + 1]


def _answer_traits(answer: str) -> set[str]:
    lowered = answer.lower()
    words = re.findall(r"\b[\w'-]+\b", lowered)
    word_count = len(words)
    traits: set[str] = set()
    no_example_markers = [
        "i don't have",
        "i do not have",
        "i cant think of",
        "i can't think of",
        "i don't think i have",
        "hypothetical",
        "i would",
        "i think i would",
    ]
    if any(marker in lowered for marker in no_example_markers):
        traits.add("no_example")
    emotional_markers = [
        "laid off",
        "stress",
        "stressed",
        "upset",
        "emotional",
        "frustrated",
        "disappointed",
        "anxious",
        "panic",
        "cry",
        "burned out",
    ]
    if any(marker in lowered for marker in emotional_markers):
        traits.add("emotional")
    if word_count < 25:
        traits.add("short")
    if word_count > 160 or lowered.startswith(("to give a little background", "so basically", "there was a time when")):
        traits.add("rambling")

    we_count = len(re.findall(r"\b(we|our|us)\b", lowered))
    i_count = len(re.findall(r"\b(i|my|me)\b", lowered))
    if we_count >= 3 and we_count > i_count * 1.5:
        traits.add("we_language")

    has_result_marker = any(
        marker in lowered
        for marker in (
            "as a result",
            "the result",
            "outcome",
            "improved",
            "reduced",
            "saved",
            "delivered",
            "shipped",
            "launched",
            "completed",
            "increased",
            "decreased",
            "faster",
        )
    ) or bool(re.search(r"\b\d+([.%x]| percent)?\b", lowered))
    if not has_result_marker:
        traits.add("missing_result")
    return traits


def _infer_star_scores(answer: str) -> tuple[dict[str, int], set[str]]:
    lowered = answer.lower()
    traits = _answer_traits(answer)
    word_count = len(re.findall(r"\b[\w'-]+\b", lowered))

    has_context = any(marker in lowered for marker in ("during", "when", "while", "project", "internship", "team", "class", "semester"))
    has_task = any(
        marker in lowered
        for marker in (
            "my role",
            "responsible",
            "my responsibility was",
            "i was responsible for",
            "i owned",
            "needed to",
            "task was",
            "goal was",
            "i had to",
        )
    )
    has_action = bool(
        re.search(
            r"\b(i|my)\b.*\b(built|created|fixed|proposed|organized|scheduled|reviewed|debugged|implemented|coordinated|mapped|interviewed|aligned|escalated|explained|documented)\b",
            lowered,
        )
    )
    has_metric = bool(re.search(r"\b\d+([.%x]| percent)?\b", lowered))
    has_result = "missing_result" not in traits

    scores = {
        "situation": 4 if has_context else 2,
        "task": 4 if has_task else 2,
        "action": 4 if has_action else (3 if " i " in f" {lowered} " else 2),
        "result": 4 if has_result else 1,
    }

    if has_metric:
        scores["result"] = 5
    if word_count < 40:
        scores = {part: min(score, 2) for part, score in scores.items()}
    if "no_example" in traits:
        scores = {"situation": 1, "task": 1, "action": 2, "result": 1}
    if "we_language" in traits:
        scores["task"] = min(scores["task"], 2)
        scores["action"] = min(scores["action"], 2)
    if "rambling" in traits:
        scores["situation"] = min(scores["situation"], 2)
    if "emotional" in traits:
        scores["result"] = min(scores["result"], 2)
    if not has_context and word_count > 80:
        scores["situation"] = 2
    if all(score >= 4 for score in scores.values()) and word_count > 55:
        scores = {part: max(score, 4) for part, score in scores.items()}
    return scores, traits


def _feedback_for_score(part: str, score: int) -> str:
    if score >= 5:
        return f"The {part} is clear, specific, and immediately credible."
    if score == 4:
        return f"The {part} is solid, but one more precise detail would make it stronger."
    if score == 3:
        return f"The {part} is present, but it still feels generic."
    if score == 2:
        return f"The {part} is vague and needs more concrete detail."
    return f"The {part} is missing or too unclear to help the interviewer."


def _infer_follow_up_intent(scores: dict[str, int], traits: set[str]) -> str:
    if "no_example" in traits:
        return "reframe_no_example"
    if "we_language" in traits:
        return "reduce_we_language"
    if "emotional" in traits:
        return "support_emotional"
    if "rambling" in traits:
        return "tighten_rambling"
    if all(score >= 4 for score in scores.values()):
        return "praise_strong"
    weakest = min(STAR_PARTS, key=lambda part: scores[part])
    return {
        "situation": "clarify_situation",
        "task": "clarify_task",
        "action": "clarify_action",
        "result": "clarify_result",
    }[weakest]


def _fallback_strengths(scores: dict[str, int], traits: set[str]) -> list[str]:
    strengths = []
    if scores["action"] >= 4:
        strengths.append("You explained your individual actions instead of only describing the team.")
    if scores["situation"] >= 4:
        strengths.append("The context is easy to follow and feels grounded in a real engineering situation.")
    if scores["result"] >= 4:
        strengths.append("You closed the story with a concrete outcome instead of stopping at effort.")
    if "emotional" in traits:
        strengths.append("You were honest about a difficult moment without losing professionalism.")
    return strengths or ["You picked a story that is directionally relevant to the question."]


def _fallback_improvements(scores: dict[str, int], traits: set[str]) -> list[str]:
    improvements = []
    if "no_example" in traits:
        improvements.append("Replace the hypothetical answer with one real story from a class, internship, project, club, or hackathon.")
    if "we_language" in traits:
        improvements.append("Use more first-person language so your ownership is unmistakable.")
    if "rambling" in traits:
        improvements.append("Shorten the setup and get to the challenge faster.")
    if "emotional" in traits:
        improvements.append("Keep the emotional context brief and spend more time on what you did and what changed.")
    for part, score in scores.items():
        if score <= 3:
            improvements.append(f"Strengthen the {part} with one more specific detail.")
    if not improvements:
        improvements.append("Add one metric or reflection if you want to make the answer even sharper.")
    return list(dict.fromkeys(improvements))[:4]


def _fallback_overall(scores: dict[str, int], traits: set[str]) -> tuple[str, str]:
    if "no_example" in traits:
        return (
            "This does not answer the question directly yet because it stays hypothetical instead of giving a real story.",
            "That is thoughtful, but interviewers usually want a real example.",
        )
    if "we_language" in traits:
        return (
            "The answer sounds collaborative, but your individual ownership is still blurry.",
            "I can hear the team effort, but I want to understand what you personally drove.",
        )
    if "rambling" in traits:
        return (
            "There is a useful example here, but the setup is longer than it needs to be and dilutes the key point.",
            "There is a solid story here. Let's tighten it so the key action lands faster.",
        )
    if "emotional" in traits:
        return (
            "The answer has real emotional weight, but it still needs a clearer professional summary of your response and learning.",
            "That sounds like a difficult experience. Let's shape it into a concise interview story.",
        )
    weak_parts = [part for part, score in scores.items() if score <= 2]
    if not weak_parts:
        return (
            "Strong answer. The ownership, actions, and impact are all clear.",
            "Great answer. You clearly articulated your contribution and the outcome.",
        )
    if weak_parts == ["result"]:
        return (
            "The story is credible, but it stops before the interviewer learns what changed because of your actions.",
            "You explained the situation and action well. Now close the loop with the outcome.",
        )
    joined = ", ".join(weak_parts)
    return (
        f"This answer has a workable example, but the {joined} portion needs more precision.",
        "The theme fits the question, but I need a more specific version to evaluate it well.",
    )


def _fallback_improved_answer(question: str, answer: str, scores: dict[str, int]) -> str:
    cleaned = _normalize_whitespace(answer)
    weakest = min(STAR_PARTS, key=lambda part: scores[part])
    if weakest == "result":
        return f"{cleaned} As a result, [add the measurable outcome or what changed]."
    if weakest == "action":
        return f"[One-sentence context.] I was responsible for [your role]. I personally [specific actions]. As a result, [outcome]."
    if weakest == "task":
        return f"[Context.] My responsibility was to [clear task tied to '{question}']. I [action]. As a result, [outcome]."
    return f"[One-sentence context for '{question}'] My role was [task]. I [action]. As a result, [outcome]."


def _fallback_response(question: str, candidate_answer: str) -> dict[str, Any]:
    scores, traits = _infer_star_scores(candidate_answer)
    intent = _infer_follow_up_intent(scores, traits)
    overall, interviewer_text = _fallback_overall(scores, traits)
    return {
        "interviewer_text": interviewer_text,
        "follow_up_question": FOLLOW_UP_BY_INTENT[intent],
        "follow_up_intent": intent,
        "scores": scores,
        "feedback": {
            "overall": overall,
            "strengths": _fallback_strengths(scores, traits),
            "improvements": _fallback_improvements(scores, traits),
            "improved_answer": _fallback_improved_answer(question, candidate_answer, scores),
        },
        "confidence": 0.35,
    }


@dataclass
class InterviewerSettings:
    examples_path: str = DEFAULT_EXAMPLES_PATH
    handoff_path: str = DEFAULT_HANDOFF_PATH
    checkpoint_path: str = DEFAULT_CHECKPOINT_PATH
    device: str = _default_device()
    dtype: str | None = None
    temperature: float = 0.2
    top_k: int = 40
    max_new_tokens: int = 220
    exemplar_count: int = 1
    primary_engine: str = os.getenv("AITT_PRIMARY_ENGINE", "local_primary")
    ollama_model: str = DEFAULT_OLLAMA_MODEL
    ollama_base_url: str = DEFAULT_OLLAMA_BASE_URL
    ollama_timeout_seconds: int = int(os.getenv("AITT_OLLAMA_TIMEOUT", "90"))
    available_engines: list[str] = field(default_factory=lambda: list(VALID_ENGINES))

    def __post_init__(self) -> None:
        self.available_engines = _resolve_engine_order(self.primary_engine, self.available_engines)


class OllamaPrimaryEngine:
    def __init__(self, model: str, base_url: str, timeout_seconds: int) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def _get_json(self, endpoint: str) -> dict[str, Any]:
        req = request.Request(f"{self.base_url}{endpoint}", method="GET")
        with request.urlopen(req, timeout=self.timeout_seconds) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))

    def _post_json(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        req = request.Request(
            f"{self.base_url}{endpoint}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with request.urlopen(req, timeout=self.timeout_seconds) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))

    def is_available(self) -> bool:
        try:
            self._get_json("/api/tags")
            return True
        except Exception:
            return False

    def generate(self, system_prompt: str, user_prompt: str, temperature: float, top_k: int) -> tuple[str, dict[str, Any], int]:
        started = time.perf_counter()
        payload = {
            "model": self.model,
            "stream": False,
            "format": OLLAMA_RESPONSE_SCHEMA,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "options": {
                "temperature": temperature,
                "top_k": top_k,
                "num_predict": 120,
            },
        }
        raw = self._post_json("/api/chat", payload)
        latency_ms = int((time.perf_counter() - started) * 1000)
        content = raw.get("message", {}).get("content", "")
        return content, raw, latency_ms

    def repair(self, raw_text: str) -> tuple[str | None, dict[str, Any] | None]:
        repair_prompt = (
            "Repair the following malformed behavioral interview evaluator output into valid JSON only. "
            "Do not add commentary. Preserve the same keys when possible: interviewer_text, follow_up_question, "
            "follow_up_intent, scores, feedback, confidence.\n\n"
            f"RAW OUTPUT:\n{raw_text}"
        )
        try:
            started = time.perf_counter()
            payload = {
                "model": self.model,
                "stream": False,
                "format": OLLAMA_RESPONSE_SCHEMA,
                "messages": [
                    {"role": "system", "content": "You fix malformed JSON and return valid JSON only."},
                    {"role": "user", "content": repair_prompt},
                ],
                "options": {
                    "temperature": 0.0,
                    "top_k": 20,
                    "num_predict": 120,
                },
            }
            raw = self._post_json("/api/chat", payload)
            _ = int((time.perf_counter() - started) * 1000)
            text = raw.get("message", {}).get("content", "")
            return text, raw
        except Exception:
            return None, None


class NanoGPTBackupEngine:
    def __init__(self, checkpoint_path: str, device: str, dtype: str) -> None:
        self.device = device
        self.dtype = dtype
        self.enc = tiktoken.get_encoding("gpt2")
        self.autocast_dtype = None
        self.model = None
        self.loaded_checkpoint = None
        self.checkpoint_path = checkpoint_path if os.path.exists(checkpoint_path) else (
            SMOKE_CHECKPOINT_PATH if os.path.exists(SMOKE_CHECKPOINT_PATH) else checkpoint_path
        )

    def _ensure_loaded(self) -> None:
        if self.model is None and os.path.exists(self.checkpoint_path):
            self._load_checkpoint(self.checkpoint_path)

    def _load_checkpoint(self, checkpoint_path: str) -> None:
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        config = GPTConfig(**checkpoint["model_args"])
        model = GPT(config)
        state_dict = checkpoint["model"]
        unwanted_prefix = "_orig_mod."
        for key, value in list(state_dict.items()):
            if key.startswith(unwanted_prefix):
                state_dict[key[len(unwanted_prefix) :]] = state_dict.pop(key)
        model.load_state_dict(state_dict)
        model.eval()
        model.to(self.device)
        self.model = model
        self.loaded_checkpoint = checkpoint_path
        if self.device.startswith("cuda"):
            self.autocast_dtype = {
                "float16": torch.float16,
                "bfloat16": torch.bfloat16,
                "float32": torch.float32,
            }[self.dtype]

    def is_available(self) -> bool:
        return os.path.exists(self.checkpoint_path)

    def _get_ctx(self):
        if self.autocast_dtype is None:
            return nullcontext()
        return torch.amp.autocast(device_type="cuda", dtype=self.autocast_dtype)

    def generate(self, prompt: str, temperature: float, top_k: int, max_new_tokens: int) -> tuple[str, int]:
        self._ensure_loaded()
        if self.model is None:
            return "", 0
        prompt_ids = self.enc.encode(prompt, allowed_special={END_OF_TEXT})
        x = torch.tensor(prompt_ids, dtype=torch.long, device=self.device)[None, ...]
        started = time.perf_counter()
        with torch.no_grad():
            with self._get_ctx():
                y = self.model.generate(x, max_new_tokens=max_new_tokens, temperature=temperature, top_k=top_k)
        latency_ms = int((time.perf_counter() - started) * 1000)
        generated_ids = y[0, len(prompt_ids) :].tolist()
        decoded = self.enc.decode(generated_ids)
        if END_OF_TEXT in decoded:
            decoded = decoded.split(END_OF_TEXT, 1)[0]
        return decoded.strip(), latency_ms


class BehavioralInterviewer:
    def __init__(self, settings: InterviewerSettings | None = None) -> None:
        self.settings = settings or InterviewerSettings()
        self.device = self.settings.device
        self.dtype = self.settings.dtype or _default_dtype(self.device)
        self.examples = _load_examples(self.settings.examples_path)
        self.rules = _load_rules(self.settings.handoff_path)
        self.primary_engine = OllamaPrimaryEngine(
            model=self.settings.ollama_model,
            base_url=self.settings.ollama_base_url,
            timeout_seconds=self.settings.ollama_timeout_seconds,
        )
        self.nanogpt_engine = NanoGPTBackupEngine(
            checkpoint_path=self.settings.checkpoint_path,
            device=self.device,
            dtype=self.dtype,
        )

    def engine_status(self) -> dict[str, Any]:
        return {
            "local_primary": {
                "runtime": "ollama",
                "model": self.settings.ollama_model,
                "base_url": self.settings.ollama_base_url,
                "available": self.primary_engine.is_available(),
            },
            "nanogpt_backup": {
                "checkpoint_path": self.nanogpt_engine.loaded_checkpoint or self.nanogpt_engine.checkpoint_path,
                "available": self.nanogpt_engine.is_available(),
            },
            "heuristic_dev": {"available": True},
        }

    def _select_exemplars(
        self,
        question: str,
        group: str,
        level: str,
        question_id: str | None = None,
    ) -> list[dict[str, Any]]:
        if not self.examples:
            return []
        question_terms = set(re.findall(r"[a-z0-9]+", question.lower()))
        scored: list[tuple[int, dict[str, Any]]] = []
        for example in self.examples:
            score = 0
            if example.get("group") == group:
                score += 6
            if example.get("level") == level:
                score += 3
            if question_id and example.get("question_id") == question_id:
                score += 8
            if example.get("answer_profile") == "strong":
                score += 3
            elif example.get("answer_profile") == "adequate":
                score += 1
            example_terms = set(re.findall(r"[a-z0-9]+", example.get("question", "").lower()))
            score += len(question_terms & example_terms)
            scored.append((score, example))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [example for score, example in scored[: self.settings.exemplar_count] if score > 0]

    def _render_exemplar(self, record: dict[str, Any]) -> str:
        feedback = record["feedback"]
        scores = feedback["star"]
        return "\n".join(
            [
                f"Example question: {record['question']}",
                f"Profile: {record.get('answer_profile', 'unknown')}",
                f"Answer: {record['candidate_answer']}",
                f"Scores: s={scores['situation']['score']} t={scores['task']['score']} a={scores['action']['score']} r={scores['result']['score']}",
                f"Intent: {feedback['follow_up_intent']}",
            ]
        )

    def _render_history(self, session_turns: list[dict[str, Any]]) -> str:
        if not session_turns:
            return "None"
        lines = []
        for turn in session_turns[-3:]:
            response = turn.get("response", {})
            lines.extend(
                [
                    f"- Previous question: {turn.get('question', '')}",
                    f"  Candidate answer: {turn.get('candidate_answer', '')}",
                    f"  Previous interviewer reply: {response.get('interviewer_text', '')}",
                    f"  Previous follow-up: {response.get('follow_up_question', '')}",
                ]
            )
        return "\n".join(lines)

    def _system_prompt(self) -> str:
        return (
            "You are a behavioral interviewer for computer science students. "
            "Evaluate answers using STAR. Score situation, task, action, and result from 1 to 5. "
            "Reward specific first-person ownership and measurable outcomes. Penalize hypothetical answers, "
            "excessive 'we' language, rambling setup, and missing results. "
            "If the answer is emotional, stay empathetic but professional. "
            "Return valid JSON only."
        )

    def _user_prompt(
        self,
        question: str,
        candidate_answer: str,
        group: str,
        level: str,
        question_metadata: dict[str, Any] | None,
        session_turns: list[dict[str, Any]],
        exemplars: list[dict[str, Any]],
    ) -> str:
        compact_metadata = {
            "question_id": (question_metadata or {}).get("question_id"),
            "tags": (question_metadata or {}).get("tags", []),
            "ideal_answer_beats": (question_metadata or {}).get("ideal_answer_beats", []),
        }
        metadata_lines = [
            f"Question: {question}",
            f"Group: {group}",
            f"Level: {level}",
            f"Metadata: {json.dumps(compact_metadata, ensure_ascii=True)}",
            "Recent session turns:",
            self._render_history(session_turns),
            "Retrieved exemplars:",
            "\n\n".join(self._render_exemplar(item) for item in exemplars) if exemplars else "None",
            "Candidate answer:",
            candidate_answer.strip(),
            (
                "Use the provided JSON schema. Keep interviewer_text under 25 words. "
                "Make the follow-up question target the weakest area. "
                "Use 1-2 short strengths and 1-2 short improvements."
            ),
        ]
        return "\n".join(metadata_lines)

    def _normalize_payload(self, payload: dict[str, Any], question: str, candidate_answer: str) -> dict[str, Any]:
        fallback = _fallback_response(question, candidate_answer)
        traits = _answer_traits(candidate_answer)

        scores_payload = payload.get("scores") or payload.get("star_scores") or {}
        scores: dict[str, int] = {}
        for part in STAR_PARTS:
            score = _coerce_score(scores_payload.get(part))
            if score is None and isinstance(scores_payload.get(part), dict):
                score = _coerce_score(scores_payload[part].get("score") or scores_payload[part].get("rating"))
            scores[part] = score if score is not None else fallback["scores"][part]

        raw_intent = payload.get("follow_up_intent")
        intent = raw_intent
        if not isinstance(intent, str) or intent not in VALID_INTENTS:
            intent = _infer_follow_up_intent(scores, traits)
        if intent not in VALID_INTENTS:
            intent = fallback["follow_up_intent"]

        if "no_example" not in traits and "emotional" not in traits and "we_language" not in traits and "rambling" not in traits:
            weakest = min(STAR_PARTS, key=lambda part: scores[part])
            weakest_intent = {
                "situation": "clarify_situation",
                "task": "clarify_task",
                "action": "clarify_action",
                "result": "clarify_result",
            }[weakest]
            if not all(score >= 4 for score in scores.values()):
                intent = weakest_intent

        feedback_payload = payload.get("feedback") if isinstance(payload.get("feedback"), dict) else {}
        strengths = feedback_payload.get("strengths")
        if not isinstance(strengths, list):
            strengths = fallback["feedback"]["strengths"]
        strengths = [str(item).strip() for item in strengths if str(item).strip()][:4]

        improvements = feedback_payload.get("improvements")
        if not isinstance(improvements, list):
            improvements = fallback["feedback"]["improvements"]
        improvements = [str(item).strip() for item in improvements if str(item).strip()][:4]

        interviewer_text = payload.get("interviewer_text")
        if (
            not isinstance(interviewer_text, str)
            or not interviewer_text.strip()
            or interviewer_text.strip() == question.strip()
            or interviewer_text.strip().endswith("?")
        ):
            interviewer_text = fallback["interviewer_text"]

        follow_up_question = payload.get("follow_up_question")
        if (
            not isinstance(follow_up_question, str)
            or not follow_up_question.strip()
            or raw_intent != intent
        ):
            follow_up_question = FOLLOW_UP_BY_INTENT[intent]

        overall = feedback_payload.get("overall")
        if not isinstance(overall, str) or not overall.strip():
            overall = fallback["feedback"]["overall"]

        improved_answer = feedback_payload.get("improved_answer")
        if not isinstance(improved_answer, str) or not improved_answer.strip():
            improved_answer = fallback["feedback"]["improved_answer"]

        confidence_value = payload.get("confidence")
        if isinstance(confidence_value, (int, float)):
            confidence = max(0.0, min(1.0, float(confidence_value)))
        else:
            confidence = fallback["confidence"]

        return {
            "interviewer_text": interviewer_text.strip(),
            "follow_up_question": follow_up_question.strip(),
            "follow_up_intent": intent,
            "scores": scores,
            "feedback": {
                "overall": overall.strip(),
                "strengths": strengths or fallback["feedback"]["strengths"],
                "improvements": improvements or fallback["feedback"]["improvements"],
                "improved_answer": _normalize_whitespace(improved_answer),
            },
            "confidence": confidence,
        }

    def _parse_payload(self, raw_text: str, question: str, candidate_answer: str) -> dict[str, Any] | None:
        candidate = _extract_json_candidate(raw_text)
        if candidate is None:
            return None
        try:
            payload = json.loads(candidate)
        except json.JSONDecodeError:
            return None
        if not isinstance(payload, dict):
            return None
        return self._normalize_payload(payload, question, candidate_answer)

    def _nanogpt_prompt(
        self,
        question: str,
        candidate_answer: str,
        group: str,
        level: str,
        question_metadata: dict[str, Any] | None,
        session_turns: list[dict[str, Any]],
        exemplars: list[dict[str, Any]],
    ) -> str:
        return (
            "<mode:behavioral_interview>\n"
            "<task:json_feedback>\n"
            f"<group:{group}>\n"
            f"<level:{level}>\n"
            f"<question:{question}>\n"
            f"Question metadata: {json.dumps(question_metadata or {}, ensure_ascii=True)}\n"
            f"Session history:\n{self._render_history(session_turns)}\n"
            f"Exemplars:\n{chr(10).join(self._render_exemplar(item) for item in exemplars) if exemplars else 'None'}\n"
            "Return JSON only with keys interviewer_text, follow_up_question, follow_up_intent, scores, feedback, confidence.\n"
            f"Candidate answer:\n{candidate_answer}\n"
            "{"
        )

    def _attempt_local_primary(
        self,
        question: str,
        candidate_answer: str,
        group: str,
        level: str,
        question_metadata: dict[str, Any] | None,
        session_turns: list[dict[str, Any]],
        exemplars: list[dict[str, Any]],
        temperature: float,
        top_k: int,
    ) -> dict[str, Any] | None:
        if not self.primary_engine.is_available():
            return None
        system_prompt = self._system_prompt()
        user_prompt = self._user_prompt(
            question=question,
            candidate_answer=candidate_answer,
            group=group,
            level=level,
            question_metadata=question_metadata,
            session_turns=session_turns,
            exemplars=exemplars,
        )
        try:
            raw_text, raw_model_json, latency_ms = self.primary_engine.generate(system_prompt, user_prompt, temperature, top_k)
        except Exception:
            return None
        normalized = self._parse_payload(raw_text, question, candidate_answer)
        repaired_json = None
        if normalized is None:
            repaired_text, repaired_json = self.primary_engine.repair(raw_text)
            if repaired_text:
                normalized = self._parse_payload(repaired_text, question, candidate_answer)
        if normalized is None:
            return None
        normalized["_meta"] = {
            "prompt_version": PROMPT_VERSION,
            "runtime": "ollama",
            "model": self.settings.ollama_model,
            "latency_ms": latency_ms,
            "raw_model_json": raw_model_json,
            "repaired_json": repaired_json,
        }
        normalized["engine"] = "local_primary"
        if repaired_json is not None:
            normalized["confidence"] = min(normalized["confidence"], 0.75)
        else:
            normalized["confidence"] = max(normalized["confidence"], 0.82)
        return normalized

    def _attempt_nanogpt_backup(
        self,
        question: str,
        candidate_answer: str,
        group: str,
        level: str,
        question_metadata: dict[str, Any] | None,
        session_turns: list[dict[str, Any]],
        exemplars: list[dict[str, Any]],
        temperature: float,
        top_k: int,
        max_new_tokens: int,
    ) -> dict[str, Any] | None:
        if not self.nanogpt_engine.is_available():
            return None
        prompt = self._nanogpt_prompt(
            question=question,
            candidate_answer=candidate_answer,
            group=group,
            level=level,
            question_metadata=question_metadata,
            session_turns=session_turns,
            exemplars=exemplars,
        )
        raw_text, latency_ms = self.nanogpt_engine.generate(
            prompt=prompt,
            temperature=temperature,
            top_k=top_k,
            max_new_tokens=max_new_tokens,
        )
        normalized = self._parse_payload(raw_text, question, candidate_answer)
        if normalized is None:
            return None
        normalized["_meta"] = {
            "prompt_version": PROMPT_VERSION,
            "runtime": "nanogpt",
            "checkpoint_path": self.nanogpt_engine.loaded_checkpoint,
            "latency_ms": latency_ms,
            "raw_model_json": {"raw_text": raw_text},
            "repaired_json": None,
        }
        normalized["engine"] = "nanogpt_backup"
        normalized["confidence"] = min(normalized["confidence"], 0.6)
        return normalized

    def generate_feedback(
        self,
        question: str,
        candidate_answer: str,
        group: str = "Leadership & Influence",
        level: str = "intern",
        question_id: str | None = None,
        question_metadata: dict[str, Any] | None = None,
        session_turns: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
        top_k: int | None = None,
        max_new_tokens: int | None = None,
        force_engine: str | None = None,
    ) -> dict[str, Any]:
        session_turns = session_turns or []
        exemplars = self._select_exemplars(question, group, level, question_id=question_id)
        resolved_temperature = temperature if temperature is not None else self.settings.temperature
        resolved_top_k = top_k if top_k is not None else self.settings.top_k
        resolved_tokens = max_new_tokens if max_new_tokens is not None else self.settings.max_new_tokens

        requested = [force_engine] if force_engine else self.settings.available_engines
        for engine_name in requested:
            if engine_name == "local_primary":
                response = self._attempt_local_primary(
                    question=question,
                    candidate_answer=candidate_answer,
                    group=group,
                    level=level,
                    question_metadata=question_metadata,
                    session_turns=session_turns,
                    exemplars=exemplars,
                    temperature=resolved_temperature,
                    top_k=resolved_top_k,
                )
                if response is not None:
                    return response
            elif engine_name == "nanogpt_backup":
                response = self._attempt_nanogpt_backup(
                    question=question,
                    candidate_answer=candidate_answer,
                    group=group,
                    level=level,
                    question_metadata=question_metadata,
                    session_turns=session_turns,
                    exemplars=exemplars,
                    temperature=max(0.2, resolved_temperature),
                    top_k=resolved_top_k,
                    max_new_tokens=resolved_tokens,
                )
                if response is not None:
                    return response
            elif engine_name == "heuristic_dev":
                fallback = _fallback_response(question, candidate_answer)
                fallback["engine"] = "heuristic_dev"
                fallback["_meta"] = {
                    "prompt_version": PROMPT_VERSION,
                    "runtime": "heuristic",
                    "latency_ms": 0,
                    "raw_model_json": None,
                    "repaired_json": None,
                }
                return fallback

        fallback = _fallback_response(question, candidate_answer)
        fallback["engine"] = "heuristic_dev"
        fallback["_meta"] = {
            "prompt_version": PROMPT_VERSION,
            "runtime": "heuristic",
            "latency_ms": 0,
            "raw_model_json": None,
            "repaired_json": None,
        }
        return fallback


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local behavioral interviewer")
    parser.add_argument("--question", required=True, help="Behavioral interview question")
    parser.add_argument("--answer", required=True, help="Candidate answer text")
    parser.add_argument("--group", default="Leadership & Influence")
    parser.add_argument("--level", default="intern")
    parser.add_argument("--question-id", default=None)
    parser.add_argument("--force-engine", default=None)
    args = parser.parse_args()

    interviewer = BehavioralInterviewer()
    response = interviewer.generate_feedback(
        question=args.question,
        candidate_answer=args.answer,
        group=args.group,
        level=args.level,
        question_id=args.question_id,
        force_engine=args.force_engine,
    )
    public_response = {key: value for key, value in response.items() if not key.startswith("_")}
    print(json.dumps(public_response, indent=2))


if __name__ == "__main__":
    main()
