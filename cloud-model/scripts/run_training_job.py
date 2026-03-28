"""
[AWS] SageMaker training job script.
Triggers a fine-tune of GPT-2 on behavioral interview data stored in S3.

Usage:
    python scripts/run_training_job.py

What it does:
    1. Pulls train.bin + val.bin from s3://aitt-data/behavioral_interview/
    2. Runs cloud-model/train.py with config/finetune_behavioral.py on a GPU instance
    3. Saves the checkpoint (ckpt.pt) to s3://aitt-models/behavioral/
"""

import os
import boto3
import sagemaker
from sagemaker.pytorch import PyTorch
from dotenv import load_dotenv

load_dotenv()

# [AWS] role created via: aws iam create-role --role-name AittSageMakerRole
ROLE_ARN = f"arn:aws:iam::{os.getenv('AWS_ACCOUNT_ID')}:role/AittSageMakerRole"

# [AWS] S3 paths — data bucket populated by prepare.py, model output goes to aitt-models
S3_DATA_URI    = "s3://aitt-data/behavioral_interview/"
S3_OUTPUT_URI  = "s3://aitt-models/behavioral/"

# [AWS] ml.m5.xlarge = CPU instance, free tier eligible — use for pipeline testing
# Switch to ml.g4dn.xlarge once GPU quota is approved for real training runs
INSTANCE_TYPE  = "ml.m5.xlarge"

if __name__ == "__main__":
    session = sagemaker.Session()

    estimator = PyTorch(
        # [AWS] entry_point is the existing train.py — no changes to it
        entry_point="train.py",
        source_dir="cloud-model",

        role=ROLE_ARN,
        instance_type=INSTANCE_TYPE,
        instance_count=1,

        # [AWS] PyTorch 2.0 + Python 3.10 — matches compile=False in finetune_behavioral.py
        framework_version="2.0",
        py_version="py310",

        output_path=S3_OUTPUT_URI,
        base_job_name="aitt-behavioral-finetune",

        # [AWS] pass finetune_behavioral.py as a positional argument to train.py
        # configurator.py expects: python train.py config/finetune_behavioral.py
        # SageMaker passes hyperparameters as --key value, so we use a wrapper approach
        # instead — the config path is baked into the container via environment variable
        hyperparameters={},
        environment={
            "SM_CONFIG": "config/finetune_behavioral.py",
            # [AWS] force CPU on ml.m5.xlarge — remove when switching to GPU instance
            "SM_DEVICE": "cpu",
        },
    )

    # [AWS] data channel — SageMaker downloads s3://aitt-data/behavioral_interview/
    # into /opt/ml/input/data/training/ on the instance before training starts
    estimator.fit({"training": S3_DATA_URI})

    print(f"Training job submitted: {estimator.latest_training_job.name}")
    print(f"Checkpoint will be saved to: {S3_OUTPUT_URI}")
