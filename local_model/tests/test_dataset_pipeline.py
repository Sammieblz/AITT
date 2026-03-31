from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "data" / "behavioral_interview"


class DatasetPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, str(DATASET_DIR / "prepare.py")], check=True, cwd=str(ROOT))
        cls.meta = json.loads((DATASET_DIR / "dataset_meta.json").read_text(encoding="utf-8"))
        cls.examples = json.loads((DATASET_DIR / "normalized_examples.json").read_text(encoding="utf-8"))
        cls.eval_examples = json.loads((DATASET_DIR / "eval_examples.json").read_text(encoding="utf-8"))
        cls.gold_eval = json.loads((DATASET_DIR / "gold_eval.json").read_text(encoding="utf-8"))

    def test_family_split_has_no_leakage(self) -> None:
        self.assertEqual(self.meta["train_question_family_overlap"], 0)
        train_families = set(self.meta["train_question_family_ids"])
        val_families = set(self.meta["val_question_family_ids"])
        self.assertFalse(train_families & val_families)

    def test_examples_have_canonical_schema(self) -> None:
        self.assertGreaterEqual(len(self.examples), 360)
        required = {
            "id",
            "question_id",
            "question_family_id",
            "group",
            "tags",
            "level",
            "answer_profile",
            "source_kind",
            "question",
            "candidate_answer",
            "follow_up_question",
            "feedback",
        }
        for item in self.examples[:50]:
            self.assertTrue(required.issubset(item.keys()))
            self.assertIsInstance(item["tags"], list)
            self.assertTrue(item["feedback"]["follow_up_intent"])
            for part in ("situation", "task", "action", "result"):
                self.assertIn("score", item["feedback"]["star"][part])
                self.assertIn("rating", item["feedback"]["star"][part])

    def test_eval_examples_are_from_validation_families_only(self) -> None:
        val_families = set(self.meta["val_question_family_ids"])
        self.assertTrue(self.eval_examples)
        for item in self.eval_examples:
            self.assertIn(item["question_family_id"], val_families)

    def test_gold_eval_set_size(self) -> None:
        self.assertGreaterEqual(len(self.gold_eval), 80)
        ids = {item["eval_case_id"] for item in self.gold_eval}
        self.assertEqual(len(ids), len(self.gold_eval))


if __name__ == "__main__":
    unittest.main()
