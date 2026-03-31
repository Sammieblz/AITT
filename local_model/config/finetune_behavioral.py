import time

out_dir = "out-behavioral"
eval_interval = 50
eval_iters = 25
log_interval = 10

always_save_checkpoint = True

wandb_log = False
wandb_project = "behavioral-interview"
wandb_run_name = "behavioral-" + str(int(time.time()))

dataset = "behavioral_interview"
init_from = "gpt2"

# Keep the context smaller for faster hackathon iteration.
block_size = 512
batch_size = 4
gradient_accumulation_steps = 8

# Regularize lightly; this is a narrow fine-tune.
dropout = 0.1

# Conservative GPT-2 fine-tune defaults for a small custom dataset.
learning_rate = 2e-5
weight_decay = 1e-2
max_iters = 1500
lr_decay_iters = 1500
min_lr = 2e-6
warmup_iters = 100
decay_lr = True

# Slightly larger eval cadence helps small runs.
beta2 = 0.99

# Safer default for hackathon laptops / Windows setups.
compile = False
