from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from interviewer_runtime import BehavioralInterviewer, InterviewerSettings
from content_store import ContentStore, DEFAULT_DB_PATH


_INTERVIEWER: BehavioralInterviewer | None = None
_CONTENT_STORE = ContentStore()
_CONTENT_STORE.ensure_seeded()


def _get_interviewer() -> BehavioralInterviewer:
    global _INTERVIEWER
    if _INTERVIEWER is None:
        _INTERVIEWER = BehavioralInterviewer(InterviewerSettings())
    return _INTERVIEWER


@asynccontextmanager
async def lifespan(_: FastAPI):
    _CONTENT_STORE.ensure_seeded()
    yield


app = FastAPI(
    title="AITT Interviewer API",
    version="0.4.0",
    lifespan=lifespan,
)


class GenerateTurnRequest(BaseModel):
    candidate_answer: str = Field(..., min_length=5)
    session_id: str | None = None
    question_id: str | None = None
    question: str | None = None
    group: str | None = None
    level: str | None = None
    force_engine: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    top_k: int | None = Field(default=None, ge=1, le=200)
    max_new_tokens: int | None = Field(default=None, ge=32, le=512)


class StartSessionRequest(BaseModel):
    mode: str = "behavioral"
    group: str = "Leadership & Influence"
    level: str = "intern"
    question_id: str | None = None
    question: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class FeedbackPayload(BaseModel):
    overall: str
    strengths: list[str]
    improvements: list[str]
    improved_answer: str


class GenerateTurnResponse(BaseModel):
    engine: str
    session_id: str | None = None
    question_id: str | None = None
    question: str
    group: str
    tags: list[str]
    candidate_answer: str
    interviewer_text: str
    follow_up_question: str
    follow_up_intent: str
    scores: dict[str, int]
    feedback: FeedbackPayload
    confidence: float


def _public_response(
    *,
    session_id: str | None,
    question_id: str | None,
    question: str,
    group: str,
    tags: list[str],
    candidate_answer: str,
    response: dict[str, Any],
) -> dict[str, Any]:
    return {
        "engine": response["engine"],
        "session_id": session_id,
        "question_id": question_id,
        "question": question,
        "group": group,
        "tags": tags,
        "candidate_answer": candidate_answer,
        "interviewer_text": response["interviewer_text"],
        "follow_up_question": response["follow_up_question"],
        "follow_up_intent": response["follow_up_intent"],
        "scores": response["scores"],
        "feedback": response["feedback"],
        "confidence": response["confidence"],
    }


@app.get("/health")
def health() -> dict[str, Any]:
    interviewer = _get_interviewer()
    return {
        "status": "ok",
        "db_path": str(DEFAULT_DB_PATH),
        "db_summary": _CONTENT_STORE.summary(),
        "engine_status": interviewer.engine_status(),
        "examples_loaded": len(interviewer.examples),
        "prompt_version": "behavioral_json_v2",
    }


@app.post("/content/rebuild")
def rebuild_content() -> dict[str, Any]:
    counts = _CONTENT_STORE.rebuild_content()
    return {
        "status": "rebuilt",
        "counts": counts,
        "db_path": str(DEFAULT_DB_PATH),
    }


@app.get("/content/summary")
def content_summary() -> dict[str, Any]:
    return {
        "db_path": str(DEFAULT_DB_PATH),
        "summary": _CONTENT_STORE.summary(),
    }


@app.get("/content/sections")
def list_sections() -> list[dict[str, Any]]:
    return _CONTENT_STORE.list_sections()


@app.get("/content/sections/{key}")
def get_section(key: str) -> dict[str, Any]:
    section = _CONTENT_STORE.get_section(key)
    if section is None:
        raise HTTPException(status_code=404, detail=f"Section '{key}' not found")
    return section


@app.get("/content/questions")
def list_questions(
    group: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict[str, Any]]:
    return _CONTENT_STORE.list_questions(group=group, limit=limit)


@app.get("/content/categories")
def list_categories() -> list[str]:
    return _CONTENT_STORE.list_categories()


@app.get("/content/questions/{question_id}")
def get_question(question_id: str) -> dict[str, Any]:
    question = _CONTENT_STORE.get_question(question_id)
    if question is None:
        raise HTTPException(status_code=404, detail=f"Question '{question_id}' not found")
    return question


@app.get("/content/examples")
def list_examples(
    group: str | None = None,
    level: str | None = None,
    answer_profile: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict[str, Any]]:
    return _CONTENT_STORE.list_examples(
        group=group,
        level=level,
        answer_profile=answer_profile,
        limit=limit,
    )


@app.get("/content/eval")
def list_eval_cases(
    group: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[dict[str, Any]]:
    return _CONTENT_STORE.list_eval_cases(group=group, limit=limit)


@app.post("/session/start")
def start_session(request: StartSessionRequest) -> dict[str, Any]:
    selected_question = None
    if request.question_id:
        selected_question = _CONTENT_STORE.get_question(request.question_id)
        if selected_question is None:
            raise HTTPException(status_code=404, detail=f"Question '{request.question_id}' not found")
    elif request.question:
        selected_question = {
            "question_id": None,
            "group": request.group,
            "tags": [],
            "question": request.question,
            "ideal_answer_beats": [],
        }
    else:
        selected_question = _CONTENT_STORE.pick_question(group=request.group)

    if selected_question is None:
        raise HTTPException(status_code=404, detail="No behavioral interview question is available")

    question_id = selected_question.get("question_id")
    group = selected_question.get("group", request.group)
    tags = selected_question.get("tags", [])
    question = selected_question.get("question", request.question)

    return _CONTENT_STORE.create_session(
        mode=request.mode,
        group=group,
        level=request.level,
        question_id=question_id,
        question_family_id=f"{question_id}--{request.level}" if question_id else None,
        question=question,
        tags=tags,
        metadata=request.metadata,
    )


@app.get("/session/{session_id}")
def get_session(session_id: str) -> dict[str, Any]:
    session = _CONTENT_STORE.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    return session


@app.post("/generate-turn", response_model=GenerateTurnResponse)
def generate_turn(request: GenerateTurnRequest) -> dict[str, Any]:
    interviewer = _get_interviewer()
    session = None
    if request.session_id:
        session = _CONTENT_STORE.get_session(request.session_id)
        if session is None:
            raise HTTPException(status_code=404, detail=f"Session '{request.session_id}' not found")

    selected_question = None
    if request.question_id:
        selected_question = _CONTENT_STORE.get_question(request.question_id)
        if selected_question is None:
            raise HTTPException(status_code=404, detail=f"Question '{request.question_id}' not found")
    elif request.question:
        selected_question = {
            "question_id": None,
            "group": request.group or (session["group"] if session else "Leadership & Influence"),
            "tags": [],
            "question": request.question,
            "ideal_answer_beats": [],
        }
    elif session and session.get("question"):
        question_id = session.get("question_id")
        selected_question = _CONTENT_STORE.get_question(question_id) if question_id else None
        if selected_question is None:
            selected_question = {
                "question_id": question_id,
                "group": session["group"],
                "tags": session.get("tags", []),
                "question": session["question"],
                "ideal_answer_beats": [],
            }
    else:
        selected_question = _CONTENT_STORE.pick_question(group=request.group or (session["group"] if session else None))

    if selected_question is None:
        raise HTTPException(status_code=404, detail="No question available for this turn")

    question = selected_question["question"]
    question_id = selected_question.get("question_id")
    group = selected_question.get("group") or request.group or (session["group"] if session else "Leadership & Influence")
    tags = selected_question.get("tags", [])
    level = request.level or (session["level"] if session else "intern")
    session_turns = _CONTENT_STORE.get_recent_turns(request.session_id, limit=3) if request.session_id else []

    response = interviewer.generate_feedback(
        question=question,
        candidate_answer=request.candidate_answer,
        group=group,
        level=level,
        question_id=question_id,
        question_metadata=selected_question,
        session_turns=session_turns,
        temperature=request.temperature,
        top_k=request.top_k,
        max_new_tokens=request.max_new_tokens,
        force_engine=request.force_engine,
    )

    if request.session_id:
        _CONTENT_STORE.record_turn(
            session_id=request.session_id,
            question_id=question_id,
            question=question,
            candidate_answer=request.candidate_answer,
            response=response,
        )

    return _public_response(
        session_id=request.session_id,
        question_id=question_id,
        question=question,
        group=group,
        tags=tags,
        candidate_answer=request.candidate_answer,
        response=response,
    )
