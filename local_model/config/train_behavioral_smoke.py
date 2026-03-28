out_dir = "out-behavioral-smoke"
eval_interval = 1
eval_iters = 1
log_interval = 1

always_save_checkpoint = True

wandb_log = False

dataset = "behavioral_interview"
init_from = "scratch"

batch_size = 2
gradient_accumulation_steps = 1
block_size = 256

n_layer = 4
n_head = 4
n_embd = 128
dropout = 0.1
bias = False

learning_rate = 1e-3
weight_decay = 1e-2
max_iters = 2
lr_decay_iters = 2
min_lr = 1e-4
warmup_iters = 1
decay_lr = True

device = "cpu"
dtype = "float32"
compile = False
