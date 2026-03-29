"""
[AWS] SageMaker inference handler for the fine-tuned GPT-2 behavioral interviewer.

SageMaker calls:
    model_fn()    — once at startup to load the model
    predict_fn()  — on every request to generate a response

Request format (JSON):
    {
        "prompt": "<mode:behavioral_interview>\n<role:interviewer>\nTell me about a time...\n<role:candidate>\n{candidate_answer}\n<role:interviewer_feedback>"
    }

Response format (JSON):
    {
        "feedback": "Overall: ..."
    }
"""

import os
import json
import pickle
import torch
import tiktoken
from model import GPTConfig, GPT


def model_fn(model_dir):
    """Load the fine-tuned GPT-2 checkpoint from /opt/ml/model/"""
    device = "cuda" if torch.cuda.is_available() else "cpu"

    ckpt_path = os.path.join(model_dir, "ckpt.pt")
    checkpoint = torch.load(ckpt_path, map_location=device)

    model_args = checkpoint["model_args"]
    gptconf = GPTConfig(**model_args)
    model = GPT(gptconf)

    # fix compiled model key prefix if present
    state_dict = checkpoint["model"]
    for k in list(state_dict.keys()):
        if k.startswith("_orig_mod."):
            state_dict[k[len("_orig_mod."):]] = state_dict.pop(k)

    model.load_state_dict(state_dict)
    model.eval()
    model.to(device)

    # [AWS] return model + tokenizer together so predict_fn has both
    enc = tiktoken.get_encoding("gpt2")
    return {"model": model, "enc": enc, "device": device}


def predict_fn(data, model_artifacts):
    """Generate feedback given a candidate's answer prompt."""
    model  = model_artifacts["model"]
    enc    = model_artifacts["enc"]
    device = model_artifacts["device"]

    prompt       = data.get("prompt", "")
    max_tokens   = data.get("max_new_tokens", 300)
    temperature  = data.get("temperature", 0.8)
    top_k        = data.get("top_k", 50)

    input_ids = enc.encode(prompt, allowed_special={"<|endoftext|>"})
    x = torch.tensor(input_ids, dtype=torch.long, device=device).unsqueeze(0)

    with torch.no_grad():
        y = model.generate(x, max_tokens, temperature=temperature, top_k=top_k)

    output_ids = y[0].tolist()[len(input_ids):]
    feedback = enc.decode(output_ids)

    # [AWS] strip everything from <|endoftext|> onward to prevent transcript looping
    if "<|endoftext|>" in feedback:
        feedback = feedback.split("<|endoftext|>")[0].strip()

    return {"feedback": feedback}


def input_fn(request_body, content_type="application/json"):
    """Parse incoming request."""
    if content_type == "application/json":
        return json.loads(request_body)
    raise ValueError(f"Unsupported content type: {content_type}")


def output_fn(prediction, accept="application/json"):
    """Serialize response."""
    return json.dumps(prediction), accept
