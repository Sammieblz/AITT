# Local Model Architecture

## Purpose

AITT is split into two backend workspaces:

- `local_model/`: training, dataset generation, and owned checkpoints
- `local-services/interviewer-api/`: runtime orchestration, HTTP APIs, and SQLite persistence

The `local_model/` workspace owns:

- dataset preparation
- the backup Transformer fine-tune
- the model code imported by the backup engine

The `local-services/interviewer-api/` workspace owns:

- the FastAPI surface
- engine selection across `local_primary`, `nanogpt_backup`, and `heuristic_dev`
- SQLite-backed content/session storage

## Current Engine Design

The runtime in [`../local-services/interviewer-api/interviewer_runtime.py`](../local-services/interviewer-api/interviewer_runtime.py)
uses three engines in order:

1. `local_primary`
   Uses Ollama with `qwen2.5:1.5b-instruct-q4_0`
2. `nanogpt_backup`
   Uses the owned decoder-only Transformer checkpoint from `local_model`
3. `heuristic_dev`
   Uses deterministic STAR heuristics for fallback and tests

## Does It Still Use The Transformer Pipeline?

Yes.

The backup path still uses:

- [`../local_model/model.py`](../local_model/model.py)
- [`../local_model/train.py`](../local_model/train.py)
- GPT-2 tokenization
- `train.bin` and `val.bin`
- `config/finetune_behavioral.py`

The service move does not remove the Transformer path. It relocates runtime API
ownership into `local-services`.

## Request Flow

1. The browser calls a same-origin Next API route.
2. The Next route handler calls `local-services/interviewer-api`.
3. The service loads question/session metadata from SQLite.
4. The runtime retrieves exemplar examples from `local_model/data/behavioral_interview/normalized_examples.json`.
5. The primary engine is attempted first.
6. If that fails, the backup Transformer is attempted.
7. If that fails, the heuristic engine returns a deterministic response.
8. The final response is stored in SQLite and returned through Next to the app.

## Persistence Layer

The runtime database is:

- `local-services/interviewer-api/runtime/behavioral_content.db`

It stores:

- content sections
- question bank entries
- normalized examples
- gold eval cases
- interview sessions
- interview turns

The app should consume this state only through the Python API, not by opening
the database file directly.
