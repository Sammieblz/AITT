## behavioral_interview dataset

This dataset trains a local behavioral interviewer that can:

- ask or continue a behavioral interview
- evaluate a candidate answer using the STAR method
- produce a short spoken interviewer reply
- ask a useful follow-up question
- suggest an improved answer

### Data entry rules

Do **not** scrape interview websites blindly.

Use public career-center guides only as references, then:

- author or paraphrase questions yourself
- write your own candidate answers
- write your own STAR ratings and feedback
- keep `source_url` for traceability only

### Supported input formats

`prepare.py` supports two source formats:

1. **Single-example format**
   One line in a `.jsonl` file equals one training example.

2. **Question-bank format**
   One record in a `.source.json` file defines one question and a `variants` array.
   This is the preferred format because it lets you create strong and weak
   variants for the same question without repeating shared fields.

### Preferred question-bank schema

Each record in a `.source.json` file can look like this:

```json
{
  "id": "team-conflict",
  "question_id": "coworker_conflict",
  "question_family_id": "coworker_conflict--intern",
  "source_url": "https://example.edu/interview-guide",
  "group": "Conflict & Collaboration",
  "tags": ["collaboration", "communication", "conflict", "teamwork"],
  "source_kind": "authored_seed",
  "level": "intern",
  "question": "Tell me about a time you had a conflict with a teammate.",
  "variants": [
    {
      "answer_profile": "strong",
      "quality": "strong",
      "candidate_answer": "During my software engineering class...",
      "follow_up_question": "What would you do differently next time?",
      "feedback": {
        "interviewer_reply": "Thanks. You handled that conflict thoughtfully and kept the team moving.",
        "overall": "Strong ownership and action. The result is clear but could be quantified even more.",
        "follow_up_intent": "clarify_result",
        "star": {
          "situation": {
            "score": 5,
            "rating": "strong",
            "feedback": "Clear context and stakes."
          },
          "task": {
            "score": 5,
            "rating": "strong",
            "feedback": "Your role was explicit."
          },
          "action": {
            "score": 5,
            "rating": "strong",
            "feedback": "You described what you personally did."
          },
          "result": {
            "score": 4,
            "rating": "good",
            "feedback": "The outcome is clear, but one measurable detail would make it stronger."
          }
        },
        "strengths": [
          "You showed ownership.",
          "You stayed collaborative instead of blaming others."
        ],
        "improvements": [
          "Add one measurable outcome.",
          "End with a brief reflection."
        ],
        "improved_answer": "In my software engineering class..."
      }
    }
  ]
}
```

### STAR ratings

Allowed ratings:

- `strong`
- `good`
- `weak`
- `missing`

Each STAR component can include either:

- `score` in the range `1-5`
- `rating` in `strong|good|weak|missing`

`prepare.py` normalizes both into canonical `score` + `rating` output.

### How `prepare.py` expands the data

For each normalized example, `prepare.py` creates multiple training sequences:

- a full feedback transcript
- a reply-focused transcript
- an improve-answer transcript

This gives the backup nanoGPT model more examples to learn from even when the
hand-built dataset is still relatively small.

`prepare.py` also:

- regenerates `generated_corpus.source.json` from the reviewed question bank
- writes `question_catalog.json` and `gold_eval.json`
- splits by `question_family_id`, not by individual example
- emits `eval_examples.json` for validation-only retrieval/evaluation

### Outputs

Running `prepare.py` writes:

- `train.bin`
- `val.bin`
- `dataset_meta.json`
- `normalized_examples.json`
- `eval_examples.json`
- `question_catalog.json`
- `gold_eval.json`

### Hackathon target size

Current robust-local target:

- 60 question families
- 6 answer profiles per family
- 360+ normalized examples
- 80+ gold eval cases

That gives the local runtime enough coverage for retrieval, gold-set checks, and
a narrow backup fine-tune instead of relying on the original 16-example seed.
