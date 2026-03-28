from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

SERVICE_DIR = Path(__file__).resolve().parent
REPO_ROOT = SERVICE_DIR.parents[1]
DEFAULT_DATASET_DIR = Path(
    os.getenv("AITT_BEHAVIORAL_DATA_DIR", str(REPO_ROOT / "local_model" / "data" / "behavioral_interview"))
).resolve()
DEFAULT_DB_PATH = Path(
    os.getenv("AITT_INTERVIEWER_DB_PATH", str(SERVICE_DIR / "runtime" / "behavioral_content.db"))
).resolve()
DATASET_DIR = DEFAULT_DATASET_DIR
QUESTION_BANK_PATH = DATASET_DIR / "question_bank.json"
QUESTION_CATALOG_PATH = DATASET_DIR / "question_catalog.json"
NORMALIZED_EXAMPLES_PATH = DATASET_DIR / "normalized_examples.json"
GOLD_EVAL_PATH = DATASET_DIR / "gold_eval.json"
HANDOFF_PATH = DATASET_DIR / "researcher_handoff.md"
FOUNDATION_PATH = DATASET_DIR / "behavioral_content_foundation.md"
SCHEMA_VERSION = 2


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _json_or_empty(value: str | None) -> Any:
    if not value:
        return None
    return json.loads(value)


class ContentStore:
    def __init__(self, db_path: str | os.PathLike[str] = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def _connection(self):
        conn = self._connect()
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if version != SCHEMA_VERSION:
                self._drop_schema(conn)
                self._create_schema(conn)
                conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")

    def _drop_schema(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            DROP TABLE IF EXISTS interview_turns;
            DROP TABLE IF EXISTS interview_sessions;
            DROP TABLE IF EXISTS gold_eval_cases;
            DROP TABLE IF EXISTS normalized_examples;
            DROP TABLE IF EXISTS question_bank;
            DROP TABLE IF EXISTS content_sections;
            """
        )

    def _create_schema(self, conn: sqlite3.Connection) -> None:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS content_sections (
                key TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source_path TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS question_bank (
                question_id TEXT PRIMARY KEY,
                group_name TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                question TEXT NOT NULL,
                ideal_answer_beats_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS normalized_examples (
                example_id TEXT PRIMARY KEY,
                record_id TEXT NOT NULL,
                question_id TEXT NOT NULL,
                question_family_id TEXT NOT NULL,
                group_name TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                level TEXT NOT NULL,
                answer_profile TEXT NOT NULL,
                quality TEXT NOT NULL,
                source_kind TEXT NOT NULL,
                source_url TEXT NOT NULL,
                question TEXT NOT NULL,
                candidate_answer TEXT NOT NULL,
                follow_up_question TEXT NOT NULL,
                follow_up_intent TEXT NOT NULL,
                feedback_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS gold_eval_cases (
                eval_case_id TEXT PRIMARY KEY,
                question_id TEXT NOT NULL,
                question_family_id TEXT NOT NULL,
                group_name TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                level TEXT NOT NULL,
                answer_profile TEXT NOT NULL,
                question TEXT NOT NULL,
                candidate_answer TEXT NOT NULL,
                expected_follow_up_intent TEXT NOT NULL,
                expected_scores_json TEXT NOT NULL,
                notes_json TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS interview_sessions (
                session_id TEXT PRIMARY KEY,
                mode TEXT NOT NULL,
                question_id TEXT,
                question_family_id TEXT,
                group_name TEXT NOT NULL,
                level TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                question TEXT,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS interview_turns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                turn_index INTEGER NOT NULL,
                question_id TEXT,
                question TEXT NOT NULL,
                candidate_answer TEXT NOT NULL,
                engine TEXT NOT NULL,
                prompt_version TEXT,
                raw_model_json TEXT,
                repaired_json TEXT,
                response_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(session_id) REFERENCES interview_sessions(session_id)
            );
            """
        )

    def rebuild_content(self) -> dict[str, int]:
        question_bank = _read_json(QUESTION_CATALOG_PATH) if QUESTION_CATALOG_PATH.exists() else []
        if not question_bank and QUESTION_BANK_PATH.exists():
            raw_bank = _read_json(QUESTION_BANK_PATH)
            question_bank = [
                {
                    "question_id": f"legacy-{idx}",
                    "group": item["category"],
                    "tags": [],
                    "question": item["question"],
                    "ideal_answer_beats": item["ideal_answer_beats"],
                }
                for idx, item in enumerate(raw_bank, start=1)
            ]
        normalized_examples = _read_json(NORMALIZED_EXAMPLES_PATH) if NORMALIZED_EXAMPLES_PATH.exists() else []
        gold_eval_cases = _read_json(GOLD_EVAL_PATH) if GOLD_EVAL_PATH.exists() else []
        handoff = _read_text(HANDOFF_PATH) if HANDOFF_PATH.exists() else ""
        foundation = _read_text(FOUNDATION_PATH) if FOUNDATION_PATH.exists() else ""
        timestamp = _utc_now()

        with self._connection() as conn:
            conn.execute("DELETE FROM content_sections")
            conn.execute("DELETE FROM question_bank")
            conn.execute("DELETE FROM normalized_examples")
            conn.execute("DELETE FROM gold_eval_cases")

            sections = [
                ("researcher_handoff", "Researcher Handoff", handoff, str(HANDOFF_PATH)),
                ("behavioral_foundation", "Behavioral Content Foundation", foundation, str(FOUNDATION_PATH)),
            ]
            conn.executemany(
                """
                INSERT INTO content_sections (key, title, content, source_path, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                [(key, title, content, source_path, timestamp) for key, title, content, source_path in sections],
            )

            conn.executemany(
                """
                INSERT INTO question_bank (question_id, group_name, tags_json, question, ideal_answer_beats_json)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (
                        item["question_id"],
                        item["group"],
                        json.dumps(item.get("tags", [])),
                        item["question"],
                        json.dumps(item["ideal_answer_beats"]),
                    )
                    for item in question_bank
                ],
            )

            conn.executemany(
                """
                INSERT INTO normalized_examples (
                    example_id, record_id, question_id, question_family_id, group_name, tags_json,
                    level, answer_profile, quality, source_kind, source_url, question,
                    candidate_answer, follow_up_question, follow_up_intent, feedback_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        item["id"],
                        item["record_id"],
                        item["question_id"],
                        item["question_family_id"],
                        item["group"],
                        json.dumps(item["tags"]),
                        item["level"],
                        item["answer_profile"],
                        item["quality"],
                        item["source_kind"],
                        item.get("source_url", ""),
                        item["question"],
                        item["candidate_answer"],
                        item["follow_up_question"],
                        item["feedback"]["follow_up_intent"],
                        json.dumps(item["feedback"]),
                    )
                    for item in normalized_examples
                ],
            )

            conn.executemany(
                """
                INSERT INTO gold_eval_cases (
                    eval_case_id, question_id, question_family_id, group_name, tags_json, level,
                    answer_profile, question, candidate_answer, expected_follow_up_intent,
                    expected_scores_json, notes_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        item["eval_case_id"],
                        item["question_id"],
                        item["question_family_id"],
                        item["group"],
                        json.dumps(item["tags"]),
                        item["level"],
                        item["answer_profile"],
                        item["question"],
                        item["candidate_answer"],
                        item["expected_follow_up_intent"],
                        json.dumps(item["expected_scores"]),
                        json.dumps(item.get("notes", {})),
                    )
                    for item in gold_eval_cases
                ],
            )

        return {
            "sections": len(sections),
            "questions": len(question_bank),
            "examples": len(normalized_examples),
            "gold_eval_cases": len(gold_eval_cases),
        }

    def ensure_seeded(self) -> dict[str, int]:
        with self._connection() as conn:
            row = conn.execute("SELECT COUNT(*) AS question_count FROM question_bank").fetchone()
        if row is None or row["question_count"] == 0:
            return self.rebuild_content()
        return self.summary()

    def summary(self) -> dict[str, int]:
        tables = (
            "content_sections",
            "question_bank",
            "normalized_examples",
            "gold_eval_cases",
            "interview_sessions",
            "interview_turns",
        )
        with self._connection() as conn:
            summary = {
                table: conn.execute(f"SELECT COUNT(*) AS count FROM {table}").fetchone()["count"]
                for table in tables
            }
        return summary

    def list_sections(self) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT key, title, source_path, updated_at FROM content_sections ORDER BY title"
            ).fetchall()
        return [dict(row) for row in rows]

    def get_section(self, key: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(
                "SELECT key, title, content, source_path, updated_at FROM content_sections WHERE key = ?",
                (key,),
            ).fetchone()
        return dict(row) if row else None

    def list_questions(self, group: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        query = """
            SELECT question_id, group_name, tags_json, question, ideal_answer_beats_json
            FROM question_bank
        """
        params: list[Any] = []
        if group:
            query += " WHERE group_name = ?"
            params.append(group)
        query += " ORDER BY group_name, question_id LIMIT ?"
        params.append(limit)
        with self._connection() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        results = []
        for row in rows:
            item = dict(row)
            item["group"] = item.pop("group_name")
            item["tags"] = json.loads(item.pop("tags_json"))
            item["ideal_answer_beats"] = json.loads(item.pop("ideal_answer_beats_json"))
            results.append(item)
        return results

    def list_categories(self) -> list[str]:
        with self._connection() as conn:
            rows = conn.execute(
                "SELECT DISTINCT group_name FROM question_bank ORDER BY group_name"
            ).fetchall()
        return [row["group_name"] for row in rows]

    def get_question(self, question_id: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT question_id, group_name, tags_json, question, ideal_answer_beats_json
                FROM question_bank
                WHERE question_id = ?
                """,
                (question_id,),
            ).fetchone()
        if row is None:
            return None
        item = dict(row)
        item["group"] = item.pop("group_name")
        item["tags"] = json.loads(item.pop("tags_json"))
        item["ideal_answer_beats"] = json.loads(item.pop("ideal_answer_beats_json"))
        return item

    def pick_question(self, group: str | None = None, question_id: str | None = None) -> dict[str, Any] | None:
        if question_id:
            return self.get_question(question_id)
        with self._connection() as conn:
            row = None
            if group and group != "general":
                row = conn.execute(
                    """
                    SELECT question_id, group_name, tags_json, question, ideal_answer_beats_json
                    FROM question_bank
                    WHERE group_name = ?
                    ORDER BY question_id
                    LIMIT 1
                    """,
                    (group,),
                ).fetchone()
            if row is None:
                row = conn.execute(
                    """
                    SELECT question_id, group_name, tags_json, question, ideal_answer_beats_json
                    FROM question_bank
                    ORDER BY question_id
                    LIMIT 1
                    """
                ).fetchone()
        if row is None:
            return None
        item = dict(row)
        item["group"] = item.pop("group_name")
        item["tags"] = json.loads(item.pop("tags_json"))
        item["ideal_answer_beats"] = json.loads(item.pop("ideal_answer_beats_json"))
        return item

    def list_examples(
        self,
        group: str | None = None,
        level: str | None = None,
        answer_profile: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT example_id, record_id, question_id, question_family_id, group_name, tags_json, level,
                   answer_profile, quality, source_kind, source_url, question,
                   candidate_answer, follow_up_question, follow_up_intent, feedback_json
            FROM normalized_examples
            WHERE 1 = 1
        """
        params: list[Any] = []
        if group:
            query += " AND group_name = ?"
            params.append(group)
        if level:
            query += " AND level = ?"
            params.append(level)
        if answer_profile:
            query += " AND answer_profile = ?"
            params.append(answer_profile)
        query += " ORDER BY group_name, question_family_id, answer_profile LIMIT ?"
        params.append(limit)

        with self._connection() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        results = []
        for row in rows:
            item = dict(row)
            item["group"] = item.pop("group_name")
            item["tags"] = json.loads(item.pop("tags_json"))
            item["feedback"] = json.loads(item.pop("feedback_json"))
            results.append(item)
        return results

    def list_eval_cases(self, group: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        query = """
            SELECT eval_case_id, question_id, question_family_id, group_name, tags_json, level,
                   answer_profile, question, candidate_answer, expected_follow_up_intent,
                   expected_scores_json, notes_json
            FROM gold_eval_cases
        """
        params: list[Any] = []
        if group:
            query += " WHERE group_name = ?"
            params.append(group)
        query += " ORDER BY question_family_id, eval_case_id LIMIT ?"
        params.append(limit)
        with self._connection() as conn:
            rows = conn.execute(query, tuple(params)).fetchall()
        results = []
        for row in rows:
            item = dict(row)
            item["group"] = item.pop("group_name")
            item["tags"] = json.loads(item.pop("tags_json"))
            item["expected_scores"] = json.loads(item.pop("expected_scores_json"))
            item["notes"] = json.loads(item.pop("notes_json"))
            results.append(item)
        return results

    def create_session(
        self,
        mode: str = "behavioral",
        group: str = "Leadership & Influence",
        level: str = "intern",
        question_id: str | None = None,
        question_family_id: str | None = None,
        question: str | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        session_id = str(uuid4())
        timestamp = _utc_now()
        payload = metadata or {}
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO interview_sessions (
                    session_id, mode, question_id, question_family_id, group_name, level,
                    tags_json, question, metadata_json, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    mode,
                    question_id,
                    question_family_id,
                    group,
                    level,
                    json.dumps(tags or []),
                    question,
                    json.dumps(payload),
                    timestamp,
                    timestamp,
                ),
            )
        return self.get_session(session_id)

    def record_turn(
        self,
        session_id: str,
        question: str,
        candidate_answer: str,
        response: dict[str, Any],
        question_id: str | None = None,
    ) -> dict[str, Any]:
        timestamp = _utc_now()
        meta = response.get("_meta", {})
        public_response = {key: value for key, value in response.items() if not key.startswith("_")}

        with self._connection() as conn:
            session_row = conn.execute(
                """
                SELECT session_id, question_family_id
                FROM interview_sessions
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
            if session_row is None:
                raise ValueError(f"Session '{session_id}' does not exist")
            existing = conn.execute(
                "SELECT COUNT(*) AS count FROM interview_turns WHERE session_id = ?",
                (session_id,),
            ).fetchone()
            turn_index = existing["count"] + 1
            conn.execute(
                """
                INSERT INTO interview_turns (
                    session_id, turn_index, question_id, question, candidate_answer,
                    engine, prompt_version, raw_model_json, repaired_json, response_json, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    turn_index,
                    question_id,
                    question,
                    candidate_answer,
                    public_response.get("engine", "unknown"),
                    meta.get("prompt_version"),
                    json.dumps(meta.get("raw_model_json")) if meta.get("raw_model_json") is not None else None,
                    json.dumps(meta.get("repaired_json")) if meta.get("repaired_json") is not None else None,
                    json.dumps(public_response),
                    timestamp,
                ),
            )
            conn.execute(
                """
                UPDATE interview_sessions
                SET question_id = COALESCE(?, question_id),
                    question = ?,
                    updated_at = ?
                WHERE session_id = ?
                """,
                (question_id, question, timestamp, session_id),
            )
        return self.get_session(session_id)

    def list_session_turns(self, session_id: str) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT id, turn_index, question_id, question, candidate_answer,
                       engine, prompt_version, raw_model_json, repaired_json,
                       response_json, created_at
                FROM interview_turns
                WHERE session_id = ?
                ORDER BY turn_index
                """,
                (session_id,),
            ).fetchall()
        turns = []
        for row in rows:
            item = dict(row)
            item["response"] = json.loads(item.pop("response_json"))
            item["raw_model_json"] = _json_or_empty(item.get("raw_model_json"))
            item["repaired_json"] = _json_or_empty(item.get("repaired_json"))
            turns.append(item)
        return turns

    def get_recent_turns(self, session_id: str, limit: int = 3) -> list[dict[str, Any]]:
        with self._connection() as conn:
            rows = conn.execute(
                """
                SELECT id, turn_index, question_id, question, candidate_answer,
                       engine, prompt_version, response_json, created_at
                FROM interview_turns
                WHERE session_id = ?
                ORDER BY turn_index DESC
                LIMIT ?
                """,
                (session_id, limit),
            ).fetchall()
        turns = []
        for row in reversed(rows):
            item = dict(row)
            item["response"] = json.loads(item.pop("response_json"))
            turns.append(item)
        return turns

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        with self._connection() as conn:
            row = conn.execute(
                """
                SELECT session_id, mode, question_id, question_family_id, group_name, level,
                       tags_json, question, metadata_json, created_at, updated_at
                FROM interview_sessions
                WHERE session_id = ?
                """,
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        session = dict(row)
        session["group"] = session.pop("group_name")
        session["tags"] = json.loads(session.pop("tags_json"))
        session["metadata"] = json.loads(session.pop("metadata_json"))
        session["turns"] = self.list_session_turns(session_id)
        return session
