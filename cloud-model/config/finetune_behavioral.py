import time

# [AWS] out_dir is intentionally NOT set here — train.py sets it to /opt/ml/model on SageMaker
# out_dir = "out-behavioral"  # use this for local runs only
eval_interval = 25
eval_iters = 20
log_interval = 5

always_save_checkpoint = True  # [AWS] ensure checkpoint is saved for pipeline testing

wandb_log = False
wandb_project = "behavioral-interview"
wandb_run_name = "behavioral-" + str(int(time.time()))

dataset = "behavioral_interview"
init_from = "gpt2"

# Keep the context smaller for faster hackathon iteration.
# [AWS] reduced block_size to 64 for pipeline testing with minimal seed data (522 tokens)
# increase back to 512 once real training data is available
block_size = 64
batch_size = 1
gradient_accumulation_steps = 1

# Regularize lightly; this is a narrow fine-tune.
dropout = 0.1

# Conservative GPT-2 fine-tune defaults for a small custom dataset.
learning_rate = 3e-5
# [AWS] reduced for pipeline smoke test — restore to 600 with real data
max_iters = 10
lr_decay_iters = 10
eval_interval = 5  # [AWS] eval at iter 5 so checkpoint gets written within 10 iters
min_lr = 3e-6
warmup_iters = 25
decay_lr = True

# Slightly larger eval cadence helps small runs.
beta2 = 0.99

# Safer default for hackathon laptops / Windows setups.
compile = False
