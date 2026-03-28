from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
for path in (ROOT, REPO_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import app as interviewer_api_app  # noqa: E402
from interviewer_runtime import InterviewerSettings, _resolve_engine_order  # noqa: E402


class BehavioralServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(interviewer_api_app.app)

    def test_content_endpoints_return_stable_shapes(self) -> None:
        categories = self.client.get("/content/categories")
        self.assertEqual(categories.status_code, 200)
        self.assertTrue(categories.json())

        questions = self.client.get("/content/questions?limit=3")
        self.assertEqual(questions.status_code, 200)
        self.assertEqual(len(questions.json()), 3)
        self.assertIn("question_id", questions.json()[0])

        examples = self.client.get("/content/examples?limit=3")
        self.assertEqual(examples.status_code, 200)
        self.assertEqual(len(examples.json()), 3)
        self.assertIn("answer_profile", examples.json()[0])

    def test_session_turn_is_persisted(self) -> None:
        session = self.client.post(
            "/session/start",
            json={"group": "Leadership & Influence", "level": "intern"},
        )
        self.assertEqual(session.status_code, 200)
        payload = session.json()
        session_id = payload["session_id"]

        turn = self.client.post(
            "/generate-turn",
            json={
                "session_id": session_id,
                "candidate_answer": (
                    "During my internship, the release team was slipping because nobody owned cross-team coordination. "
                    "I was responsible for keeping the delivery on track without formal authority. "
                    "I created a task board, ran short unblocker check-ins, and clarified ownership with each engineer. "
                    "As a result, we shipped on time and cut duplicate work by roughly 30 percent."
                ),
                "force_engine": "heuristic_dev",
            },
        )
        self.assertEqual(turn.status_code, 200)
        self.assertEqual(turn.json()["session_id"], session_id)

        session_after = self.client.get(f"/session/{session_id}")
        self.assertEqual(session_after.status_code, 200)
        self.assertEqual(len(session_after.json()["turns"]), 1)

    def test_behavior_specific_follow_up_intents(self) -> None:
        cases = [
            (
                "missing_result",
                "During my internship, our team kept stepping on each other's changes before a release. "
                "I was responsible for coordinating the release plan. I mapped dependencies, created a task board, "
                "and ran short unblocker check-ins.",
                "clarify_result",
            ),
            (
                "we_language",
                "During our capstone, we had a conflict with another team about the API design. "
                "We reviewed the tradeoffs, we proposed a phased approach, and we got everyone aligned. "
                "The result was better for the team.",
                "reduce_we_language",
            ),
            (
                "emotional",
                "After a reorg during my internship, I felt stressed and disappointed because my project scope changed. "
                "My role was to stabilize the handoff. I documented the service, met with the new owner, "
                "and made sure the open issues were clear, but emotionally it was difficult.",
                "support_emotional",
            ),
            (
                "no_example",
                "I do not have a perfect example of that, but I think I would stay calm, communicate clearly, and solve it with the team.",
                "reframe_no_example",
            ),
            (
                "rambling",
                "To give a little background, this happened during a period when several priorities were moving at once and there were "
                "a lot of details across teams and classes and responsibilities. During my internship, the team was behind schedule "
                "and there were multiple reasons for that. My role was to keep the work organized. I created a task board, "
                "ran unblocker check-ins, and clarified ownership. As a result, we delivered on time.",
                "tighten_rambling",
            ),
        ]
        for _, answer, expected_intent in cases:
            response = self.client.post(
                "/generate-turn",
                json={
                    "question": "Tell me about a time you led a project without formal authority.",
                    "group": "Leadership & Influence",
                    "level": "intern",
                    "candidate_answer": answer,
                    "force_engine": "heuristic_dev",
                },
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["follow_up_intent"], expected_intent)

    def test_strong_answer_gets_positive_follow_up(self) -> None:
        response = self.client.post(
            "/generate-turn",
            json={
                "question": "Tell me about a time you led a project without formal authority.",
                "group": "Leadership & Influence",
                "level": "intern",
                "candidate_answer": (
                    "During my internship, the release team was slipping because nobody owned cross-team coordination. "
                    "My responsibility was to keep the delivery on track without formal authority. "
                    "I created a task board, ran short unblocker check-ins, and clarified ownership with each engineer. "
                    "As a result, we shipped on time and cut duplicate work by roughly 30 percent."
                ),
                "force_engine": "heuristic_dev",
            },
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["follow_up_intent"], "praise_strong")
        self.assertGreaterEqual(payload["scores"]["result"], 4)


class RuntimeSettingsTests(unittest.TestCase):
    def test_primary_engine_env_reorders_default_engine_sequence(self) -> None:
        with patch.dict("os.environ", {"AITT_PRIMARY_ENGINE": "nanogpt_backup"}):
            settings = InterviewerSettings(primary_engine="nanogpt_backup")
        self.assertEqual(
            settings.available_engines,
            ["nanogpt_backup", "local_primary", "heuristic_dev"],
        )

    def test_resolve_engine_order_keeps_valid_unique_engines(self) -> None:
        resolved = _resolve_engine_order(
            "nanogpt_backup",
            ["local_primary", "nanogpt_backup", "local_primary", "heuristic_dev", "invalid"],
        )
        self.assertEqual(
            resolved,
            ["nanogpt_backup", "local_primary", "heuristic_dev"],
        )


if __name__ == "__main__":
    unittest.main()
