# Local Model

This directory contains the locally owned model workspace used by AITT.

It is responsible for:

- preparing the behavioral interview dataset
- generating a larger synthetic behavioral corpus from reviewed question families
- fine-tuning a GPT-style backup model on that dataset
- exposing owned model code and checkpoints that backend services can import

It is not responsible for:

- HTTP APIs
- SQLite runtime/session ownership
- voice

Additional repo-level documentation:

- [`../docs/README.md`](../docs/README.md)
- [`../docs/local-model-architecture.md`](../docs/local-model-architecture.md)
- [`../docs/local-model-runbook.md`](../docs/local-model-runbook.md)
- [`../docs/data-and-storage.md`](../docs/data-and-storage.md)
- [`../docs/api-and-nextjs-integration.md`](../docs/api-and-nextjs-integration.md)
- [`../docs/environment-reference.md`](../docs/environment-reference.md)
- [`../docs/repo-hygiene.md`](../docs/repo-hygiene.md)
- [`../local-services/interviewer-api/README.md`](../local-services/interviewer-api/README.md)

## Dataset Flow

Author source data in:

- `data/behavioral_interview/*.jsonl`
- `data/behavioral_interview/*.source.json`

Then build the tokenized dataset:

```powershell
cd local_model
python data\behavioral_interview\prepare.py
```

Health of the prepared dataset can be checked with:

```powershell
cd local_model
python -m unittest discover -s tests -v
```

This writes:

- `data/behavioral_interview/train.bin`
- `data/behavioral_interview/val.bin`
- `data/behavioral_interview/dataset_meta.json`
- `data/behavioral_interview/normalized_examples.json`
- `data/behavioral_interview/eval_examples.json`
- `data/behavioral_interview/question_catalog.json`
- `data/behavioral_interview/gold_eval.json`

## Training

Quick pipeline smoke test on CPU:

```powershell
cd local_model
python train.py config\train_behavioral_smoke.py
```

Backup fine-tune from GPT-2:

```powershell
cd local_model
python train.py config\finetune_behavioral.py
```

Notes:

- `config/finetune_behavioral.py` expects `transformers` because `init_from='gpt2'`
- the resulting checkpoint is written to `out-behavioral/ckpt.pt`
- the nanoGPT path is the owned backup engine, not the primary runtime API path

## What This Workspace Should Not Store

- live runtime SQLite files
- backend service logs
- frontend build artifacts

Those belong in `local-services/` or `aitt/` and are treated as disposable
runtime state.

## Service Relationship

The runtime API now lives in:

- [`../local-services/interviewer-api/`](../local-services/interviewer-api/)

That service imports the local backup Transformer path from this workspace and
uses this directory as the source of truth for:

- dataset files
- normalized examples
- question bank
- gold eval set
- checkpoints
