# Interviewer API

This service owns:

- the FastAPI behavioral interviewer HTTP surface
- runtime orchestration across `local_primary`, `nanogpt_backup`, and `heuristic_dev`
- SQLite-backed content/session persistence

It does not own:

- frontend rendering
- voice
- dataset generation or model training

Source behavioral content comes from:

- [`../../local_model/data/behavioral_interview/`](../../local_model/data/behavioral_interview/)

## Run

From the repo root:

```powershell
pip install -r local-services\interviewer-api\requirements.txt
python -m uvicorn app:app --app-dir local-services\interviewer-api --host 127.0.0.1 --port 8000
```

Health check:

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing
```

## Main Endpoints

- `GET /health`
- `GET /content/summary`
- `GET /content/sections`
- `GET /content/sections/{key}`
- `GET /content/questions`
- `GET /content/categories`
- `GET /content/questions/{id}`
- `GET /content/examples`
- `GET /content/eval`
- `POST /content/rebuild`
- `POST /session/start`
- `GET /session/{id}`
- `POST /generate-turn`

## Env

Copy `.env.example` to `.env` only if you need overrides.

Main vars:

- `AITT_PRIMARY_ENGINE`
- `AITT_INTERVIEWER_DB_PATH`
- `AITT_BEHAVIORAL_DATA_DIR`
- `AITT_OLLAMA_MODEL`
- `AITT_OLLAMA_BASE_URL`
- `AITT_OLLAMA_TIMEOUT`

## Runtime State

The service writes operational state under:

- `runtime/`
- `runtime-logs/`

These directories are generated, local-only, and should not be committed.
