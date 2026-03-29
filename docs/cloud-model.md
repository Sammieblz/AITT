# Cloud Model

## Purpose

`cloud-model/` contains the SageMaker-adapted versions of the model training and inference code. It mirrors `local_model/` but is configured to run on AWS infrastructure with S3 for data and model artifacts.

## Files

- [`../cloud-model/train.py`](../cloud-model/train.py) — SageMaker training entry point (reads `SM_CONFIG` env var)
- [`../cloud-model/inference.py`](../cloud-model/inference.py) — SageMaker inference handler
- [`../cloud-model/model.py`](../cloud-model/model.py) — GPT-2 architecture (identical to `local_model/model.py`)
- [`../cloud-model/configurator.py`](../cloud-model/configurator.py) — Hyperparameter override system
- [`../cloud-model/config/finetune_behavioral.py`](../cloud-model/config/finetune_behavioral.py) — Fine-tune config for SageMaker runs
- [`../cloud-model/scripts/run_training_job.py`](../cloud-model/scripts/run_training_job.py) — Launches a SageMaker training job

## Training Pipeline

### Data

Training data must be pre-processed and uploaded to S3 before launching a job.

Run the local prepare step to generate token files:

```bash
python local_model/data/behavioral_interview/prepare.py
```

Then upload to S3:

```bash
aws s3 cp local_model/data/behavioral_interview/train.bin s3://aitt-data/behavioral_interview/
aws s3 cp local_model/data/behavioral_interview/val.bin s3://aitt-data/behavioral_interview/
```

SageMaker downloads the `training` data channel to `/opt/ml/input/data/training/` before the job starts.

### Launching a Training Job

```bash
python cloud-model/scripts/run_training_job.py
```

This creates a SageMaker PyTorch estimator and calls `fit()`. The job:

1. Pulls `train.bin` and `val.bin` from `s3://aitt-data/behavioral_interview/`
2. Runs `cloud-model/train.py` with `config/finetune_behavioral.py`
3. Saves `ckpt.pt` to `s3://aitt-models/behavioral/`

### Instance Type

Current config:

```python
INSTANCE_TYPE = "ml.m5.xlarge"  # CPU, pipeline testing
```

Switch to `ml.g4dn.xlarge` for real training runs once GPU quota is approved.

### Training Config

Key values in [`config/finetune_behavioral.py`](../cloud-model/config/finetune_behavioral.py):

- `init_from = "gpt2"` — fine-tunes from the pre-trained GPT-2 124M checkpoint
- `block_size = 64` — reduced for pipeline testing; restore to 512 for full runs
- `batch_size = 1`
- `learning_rate = 3e-5`
- `max_iters = 1500`
- `device = "mps"` — Apple Silicon for local fine-tune; ignored on SageMaker GPU instances
- `compile = False` — safer for CPU and MPS environments

`out_dir` is not set in the config. `train.py` sets it to `/opt/ml/model/` when running on SageMaker so the checkpoint is automatically packaged into `model.tar.gz` and uploaded to S3.

## Inference Handler

`inference.py` implements the four SageMaker handler functions:

### model_fn

Called once at container startup. Loads `ckpt.pt` from `/opt/ml/model/` and initializes the GPT-2 model and tiktoken encoder. Returns a dict with `model`, `enc`, and `device`.

### predict_fn

Called on every request. Accepts:

```json
{ "prompt": "...", "max_new_tokens": 400, "temperature": 0.8, "top_k": 50 }
```

Tokenizes the prompt, runs `model.generate()`, decodes the output tokens, and strips everything from `<|endoftext|>` onward to prevent transcript looping.

Returns:

```json
{ "feedback": "generated feedback text" }
```

### input_fn / output_fn

Standard JSON parsing and serialization. Content type: `application/json`.

## Deploying After Training

Once a training job completes and the model artifact is available in S3, deploy the endpoint:

```bash
SM_MODEL_URI=s3://aitt-models/behavioral/.../output/model.tar.gz \
python cloud-services/deploy_endpoint.py
```

See [`aws-services.md`](./aws-services.md) for endpoint configuration details.

## S3 Paths

| Path | Purpose |
|------|---------|
| `s3://aitt-data/behavioral_interview/` | Training data (`train.bin`, `val.bin`) |
| `s3://aitt-models/behavioral/` | Training job output (`model.tar.gz`) |

## IAM Role

The training job and endpoint deployment use:

```
arn:aws:iam::{AWS_ACCOUNT_ID}:role/AittSageMakerRole
```

Created via:

```bash
aws iam create-role --role-name AittSageMakerRole
```

## Relationship to local_model

`cloud-model/` and `local_model/` share the same model architecture (`model.py`) and training logic (`train.py`). The differences are:

- `cloud-model/train.py` reads `SM_CONFIG` and `SM_DEVICE` env vars set by SageMaker
- `cloud-model/config/finetune_behavioral.py` omits `out_dir` so SageMaker controls the output path
- `cloud-model/` includes `inference.py` for serving; `local_model/` uses `sample.py` for local generation
- The local config in `local_model/config/finetune_behavioral.py` sets `out_dir = "out-behavioral"` and targets the local checkpoint path
