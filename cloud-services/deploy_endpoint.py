"""
[AWS] Deploy the fine-tuned GPT-2 model as a SageMaker serverless endpoint.

Usage:
    python cloud-services/deploy_endpoint.py

What it does:
    1. Finds the latest model.tar.gz in s3://aitt-models/behavioral/
    2. Creates a SageMaker model from it
    3. Deploys it as a serverless endpoint (pay per request, scales to zero)
"""

import os
import boto3
import sagemaker
from sagemaker.pytorch import PyTorchModel
from sagemaker.serverless import ServerlessInferenceConfig
from dotenv import load_dotenv

load_dotenv()

ROLE_ARN      = f"arn:aws:iam::{os.getenv('AWS_ACCOUNT_ID')}:role/AittSageMakerRole"
S3_MODEL_URI  = os.getenv("SM_MODEL_URI")  # set this after training, e.g. s3://aitt-models/behavioral/.../output/model.tar.gz
ENDPOINT_NAME = "aitt-behavioral-endpoint"

if __name__ == "__main__":
    session = sagemaker.Session()

    model = PyTorchModel(
        model_data=S3_MODEL_URI,
        role=ROLE_ARN,
        entry_point="inference.py",
        # [AWS] source_dir points to cloud-model so model.py is available to inference.py
        source_dir="cloud-model",
        framework_version="2.0",
        py_version="py310",
        name="aitt-behavioral-model",
    )

    # [AWS] 6144MB (6GB) needed to load GPT-2 124M model weights + inference overhead on CPU
    serverless_config = ServerlessInferenceConfig(
        memory_size_in_mb=6144,
        max_concurrency=5,
    )

    predictor = model.deploy(
        serverless_inference_config=serverless_config,
        endpoint_name=ENDPOINT_NAME,
    )

    print(f"Endpoint deployed: {ENDPOINT_NAME}")
    print(f"Call it via: POST https://runtime.sagemaker.{os.getenv('AWS_DEFAULT_REGION')}.amazonaws.com/endpoints/{ENDPOINT_NAME}/invocations")
