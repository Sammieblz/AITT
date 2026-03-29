# Repo Hygiene

This repo contains both source assets and machine-local runtime artifacts. Only
the source assets should be committed.

## Safe To Commit

- application code in `aitt/`
- backend service code in `local-services/`
- training/data-prep code in `local_model/`
- authored behavioral source data
- generated JSON metadata that is part of the curated dataset handoff
- markdown documentation

## Should Not Be Committed

- `aitt/node_modules/`
- `aitt/.next/`
- runtime SQLite files
- runtime log files
- Python `__pycache__` folders
- transient dev logs
- local checkpoints in `local_model/out-*`
- local `.env` files containing machine-specific values

## Runtime Directories To Treat As Disposable

- `local-services/interviewer-api/runtime/`
- `local-services/interviewer-api/runtime-logs/`
- `local_model/out-behavioral/`
- `local_model/out-behavioral-smoke/`

If these directories exist locally, they are expected to be regenerated. They
are operational state, not source.

## Stale Artifact Note

The old database path under
`local_model/data/behavioral_interview/behavioral_content.db` is a stale local
artifact from the pre-service split. The live runtime now stores session/content
state under `local-services/interviewer-api/runtime/`.

## Before Pushing

Run this quick check:

```powershell
git status --short
```

If you see runtime DBs, logs, caches, or `node_modules`, they should usually be
ignored or removed before pushing.
