# Data And Storage

## Dataset Pipeline

The behavioral dataset lives under:

- [`../local_model/data/behavioral_interview/`](../local_model/data/behavioral_interview/)

The main pipeline entrypoint is:

- [`../local_model/data/behavioral_interview/prepare.py`](../local_model/data/behavioral_interview/prepare.py)

It:

- regenerates the synthetic corpus from the reviewed question bank
- normalizes authored and generated examples into one schema
- splits by `question_family_id`
- writes `train.bin` and `val.bin`
- writes retrieval/eval JSON artifacts

## Generated Dataset Size

Current observed values from [`dataset_meta.json`](../local_model/data/behavioral_interview/dataset_meta.json):

- `376` normalized examples
- `69` question families
- `315` train examples
- `61` validation examples
- `945` train sequences
- `183` validation sequences
- `418,284` train tokens
- `80,093` validation tokens

## Gold Eval Set

The locked eval file is:

- [`../local_model/data/behavioral_interview/gold_eval.json`](../local_model/data/behavioral_interview/gold_eval.json)

It currently contains `90` cases.

## Runtime Storage

The runtime database is:

- `local-services/interviewer-api/runtime/behavioral_content.db`

It stores:

- prompt content
- question bank rows
- normalized examples
- gold eval rows
- interview sessions
- interview turns

At the current scale, this database is small enough for local development.

## What Should Be In Git

Safe to keep in repo:

- source JSON and JSONL files
- generated corpus JSON
- `dataset_meta.json`
- code
- tests
- markdown documentation

Recommended not to commit:

- runtime SQLite files
- model output directories like `local_model/out-behavioral/`
- local checkpoints
- transient runtime logs

The root [`.gitignore`](../.gitignore) covers these paths.

## Storage Cost On This Machine

The dataset artifacts themselves are modest.

The heavier local storage cost comes from model runtimes:

- Ollama model `qwen2.5:1.5b-instruct-q4_0` was observed at about `934 MB`
- local checkpoints can add more if full fine-tunes are produced

## Compute Cost On This Machine

Observed local-primary inference on this CPU is functional but slow.

- the structured Ollama path works
- one live turn was observed at roughly `20s`

Data and storage are manageable. Inference latency is the main machine-level
constraint.
