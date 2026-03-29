# AWS Services

## Purpose

`cloud-services/` is the AWS integration layer for AITT. It handles:

- Invoking the SageMaker endpoint with a candidate prompt
- Parsing structured STAR feedback from the model response
- Persisting session and turn data to DynamoDB

## Files

- [`../cloud-services/api.py`](../cloud-services/api.py) — Flask API, SageMaker invocation, response parsing
- [`../cloud-services/dynamodb.py`](../cloud-services/dynamodb.py) — DynamoDB client and table helpers
- [`../cloud-services/deploy_endpoint.py`](../cloud-services/deploy_endpoint.py) — Serverless endpoint deployment script

## API

Run locally for testing:

```bash
python cloud-services/api.py
```

### POST /interview

Request:

```json
{
  "session_id": "abc123",
  "turn_index": 1,
  "question": "Tell me about a time you led a project.",
  "answer": "...",
  "category": "leadership",
  "level": "intern"
}
```

Response:

```json
{
  "session_id": "abc123",
  "feedback": "...",
  "scores": { "situation": 4, "task": 3, "action": 2, "result": 2 },
  "interviewer_text": "...",
  "follow_up_question": "...",
  "follow_up_intent": "clarify_result"
}
```

### GET /session/\<session_id\>

Returns all turns for a session ordered by `turn_index`.

## Prompt Format

The prompt passed to SageMaker uses a transcript-style format:

```
<mode:behavioral_interview>
<level:{level}>
<category:{category}>
<role:interviewer>
{question}
<role:candidate>
{answer}
<role:interviewer_feedback>
```

This matches the format the model was fine-tuned on.

## SageMaker Endpoint

Endpoint name:

```bash
SM_ENDPOINT_NAME=aitt-behavioral-endpoint
```

The endpoint is serverless (pay-per-request, scales to zero). It expects a JSON payload:

```json
{ "prompt": "...", "max_new_tokens": 400, "temperature": 0.8 }
```

It returns:

```json
{ "feedback": "raw model output" }
```

Read timeout is set to 300s to handle cold starts.

## Deploying the Endpoint

After a training job completes and the model artifact is in S3:

```bash
SM_MODEL_URI=s3://aitt-models/behavioral/.../output/model.tar.gz \
python cloud-services/deploy_endpoint.py
```

This deploys `cloud-model/inference.py` as the handler with:

- Memory: 6144 MB (required for GPT-2 124M weights on CPU)
- Max concurrency: 5
- Framework: PyTorch 2.0 / Python 3.10

## DynamoDB Tables

Three tables store interview state:

| Table | Partition Key | Sort Key | Purpose |
|-------|--------------|----------|---------|
| `aitt-sessions` | `session_id` | — | Session metadata |
| `aitt-turns` | `session_id` | `turn_index` | Per-turn STAR scores and feedback |
| `aitt-content` | `content_type` | `content_id` | Question bank and normalized examples |

All tables use `PAY_PER_REQUEST` billing.

### Session Schema

- `session_id`, `mode`, `group`, `level`, `question_id`, `question_family_id`
- `question`, `tags`, `metadata`, `created_at`, `updated_at`

### Turn Schema

- `session_id`, `turn_index`, `question_id`, `question`, `candidate_answer`
- `engine`, `prompt_version`
- `scores` — `{ situation, task, action, result }` rated 1–5
- `interviewer_text`, `follow_up_question`, `follow_up_intent`
- `feedback` — `{ overall, strengths, improvements, improved_answer }`
- `confidence`, `response_json`, `created_at`

### Content Schema

- `content_type` — `"question"` or `"example"`
- `content_id`, `group`, `tags`, `level`, `answer_profile`, `question`, `data_json`

### Creating Tables

Tables are created on first run by calling:

```python
from dynamodb import create_tables_if_not_exist
create_tables_if_not_exist()
```

Or run directly:

```bash
python cloud-services/dynamodb.py
```

## Environment Variables

File: `cloud-services/.env` (or root `.env`)

Required:

- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_DEFAULT_REGION` — default `us-east-1`
- `AWS_ACCOUNT_ID` — used to construct the IAM role ARN
- `SM_MODEL_URI` — S3 path to `model.tar.gz` used at deploy time

Optional:

- `SM_ENDPOINT_NAME` — default `aitt-behavioral-endpoint`
- `DYNAMODB_SESSIONS_TABLE` — default `aitt-sessions`
- `DYNAMODB_TURNS_TABLE` — default `aitt-turns`
- `DYNAMODB_CONTENT_TABLE` — default `aitt-content`
