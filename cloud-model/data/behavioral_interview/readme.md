## behavioral_interview dataset

This dataset is for a behavioral mock interviewer that:

- asks a behavioral question
- reads a candidate answer
- gives STAR-based feedback
- asks a useful follow-up

### Do not scrape interview websites blindly

For a hackathon, the safest and fastest approach is:

- use public career-center guides as references
- manually author or paraphrase question prompts
- write your own feedback/rubrics
- keep a `source_url` field only for your own traceability

Avoid copying large amounts of proprietary interview content verbatim.

### File format

Put one or more `.jsonl` files in this folder. Each line is one JSON object.

Starter example fields:

```json
{
  "id": "team-conflict-001",
  "source_url": "https://example.edu/interview-guide",
  "category": "teamwork",
  "level": "intern",
  "question": "Tell me about a time you had a conflict with a teammate.",
  "candidate_answer": "During my software engineering class, my teammate and I disagreed on how to split up the backend work...",
  "feedback": {
    "overall": "Good example and strong ownership, but the result needs a measurable outcome.",
    "star": {
      "situation": "Clear context. You explained the class project and why the disagreement mattered.",
      "task": "Mostly clear, but you can state your exact responsibility more directly.",
      "action": "Strong. You described initiating a meeting, proposing a split, and documenting the plan.",
      "result": "Weak. Add a concrete result such as grade improvement, delivery timing, or reduced bugs."
    },
    "strengths": [
      "You sounded calm and collaborative.",
      "You explained what you personally did instead of only what the team did."
    ],
    "improvements": [
      "State your specific role in one sentence.",
      "Quantify the outcome."
    ],
    "improved_answer": "In my software engineering class, I worked on a four-person web app project..."
  },
  "follow_up_question": "What specifically changed after you stepped in, and how did you measure that result?"
}
```

### How `prepare.py` uses this

`prepare.py` reads all `.jsonl` files in this directory, validates them, renders each record into transcript-like text, tokenizes with GPT-2 BPE, and writes:

- `train.bin`
- `val.bin`
- `dataset_meta.json`

It intentionally does **not** write `meta.pkl`, because this dataset uses GPT-2 BPE rather than a custom char-level vocabulary.

### Recommended dataset size for the hackathon

Aim for:

- 40 to 60 distinct behavioral questions
- 3 to 8 answer/feedback variants per question
- 200 to 400 total records

That is enough to fine-tune a small GPT-2-style interviewer for a strong demo.
