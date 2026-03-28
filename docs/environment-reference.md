# Environment Reference

This repo uses workspace-local env files rather than one shared root runtime
env.

## Frontend App

File:

- `aitt/.env.local`

Required:

- `AITT_INTERVIEWER_API_URL`
  Base URL for the interviewer backend service. In local development this is
  typically `http://127.0.0.1:8000`.

Optional:

- `NEXT_PUBLIC_APP_URL`
  Public browser origin for absolute URLs. Local default:
  `http://localhost:3000`.

## Interviewer Backend Service

File:

- `local-services/interviewer-api/.env`

Required for normal local use:

- `AITT_PRIMARY_ENGINE`
  Default engine order. `local_primary` tries Ollama first. `nanogpt_backup`
  makes the owned Transformer checkpoint the default runtime path before any
  Ollama attempt.
- `AITT_OLLAMA_MODEL`
  Default local-primary model tag.
- `AITT_OLLAMA_BASE_URL`
  Ollama HTTP base URL.
- `AITT_OLLAMA_TIMEOUT`
  Timeout in seconds for Ollama calls.

Optional:

- `AITT_INTERVIEWER_DB_PATH`
  Runtime SQLite location. Default is under
  `local-services/interviewer-api/runtime/behavioral_content.db`.
- `AITT_BEHAVIORAL_DATA_DIR`
  Absolute override for the behavioral content directory. Leave unset unless the
  repo layout changes.

## Legacy Compatibility

Some server-side helpers still accept `AITT_LOCAL_MODEL_URL` as a compatibility
fallback, but the preferred variable name is `AITT_INTERVIEWER_API_URL`.

## What Does Not Need Env Configuration

`local_model/` does not require a dedicated `.env` file for the standard
behavioral training flow. Distributed training environment variables like
`RANK`, `LOCAL_RANK`, and `WORLD_SIZE` are only relevant if you intentionally
run distributed training.
