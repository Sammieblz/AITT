import time

out_dir = "out-behavioral"
eval_interval = 25
eval_iters = 20
log_interval = 5

always_save_checkpoint = False

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
learning_rate = 3e-5
max_iters = 600
lr_decay_iters = 600
min_lr = 3e-6
warmup_iters = 25
decay_lr = True

# Slightly larger eval cadence helps small runs.
beta2 = 0.99

# Safer default for hackathon laptops / Windows setups.
compile = False
