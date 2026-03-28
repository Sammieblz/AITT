# Local Model Runbook

## Prerequisites

Observed local target environment:

- Windows
- Python 3.13
- CPU-only PyTorch
- Ollama installed locally
- Node.js with `npm`

## Workspace Roles

- `local_model/`: data prep and backup Transformer training
- `local-services/interviewer-api/`: runtime API and SQLite persistence
- `aitt/`: frontend shell and same-origin route handlers

## First-Time Setup

Prepare the model workspace:

```powershell
cd C:\Users\Samuel\MyProjects\AITT\local_model
pip install -r requirements.txt
python data\behavioral_interview\prepare.py
```

This regenerates the behavioral corpus, token files, normalized examples, and
eval artifacts.

Then install the backend service dependencies:

```powershell
cd C:\Users\Samuel\MyProjects\AITT
pip install -r local-services\interviewer-api\requirements.txt
```

And install frontend dependencies:

```powershell
cd C:\Users\Samuel\MyProjects\AITT\aitt
npm install
```

## Pull The Local Primary Model

If Ollama has no models yet:

```powershell
& 'C:\Users\Samuel\AppData\Local\Programs\Ollama\ollama.exe' pull qwen2.5:1.5b-instruct-q4_0
```

Check:

```powershell
& 'C:\Users\Samuel\AppData\Local\Programs\Ollama\ollama.exe' list
```

## Run The Interviewer Service

From the repo root:

```powershell
cd C:\Users\Samuel\MyProjects\AITT
python -m uvicorn app:app --app-dir local-services\interviewer-api --reload --port 8000
```

Useful checks:

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing
Invoke-WebRequest -Uri "http://127.0.0.1:8000/content/summary" -UseBasicParsing
```

Copy `local-services/interviewer-api/.env.example` to
`local-services/interviewer-api/.env` if you need runtime overrides.

Important service envs:

- `AITT_PRIMARY_ENGINE`
- `AITT_INTERVIEWER_DB_PATH`
- `AITT_OLLAMA_MODEL`
- `AITT_OLLAMA_BASE_URL`
- `AITT_OLLAMA_TIMEOUT`
- optional `AITT_BEHAVIORAL_DATA_DIR`

If you want to run without Ollama as the default path, set:

```bash
AITT_PRIMARY_ENGINE=nanogpt_backup
```

With that setting, the service will try the owned Transformer checkpoint first
and only fall through to other engines if needed.

## Run The Backup Transformer Training

Smoke run:

```powershell
cd C:\Users\Samuel\MyProjects\AITT\local_model
python train.py config\train_behavioral_smoke.py
```

Full backup fine-tune:

```powershell
cd C:\Users\Samuel\MyProjects\AITT\local_model
python train.py config\finetune_behavioral.py
```

## Run Tests

```powershell
cd C:\Users\Samuel\MyProjects\AITT
python -m unittest discover -s local_model\tests -v
python -m unittest discover -s local-services\interviewer-api\tests -v
```

## Run The Next.js App

In another terminal:

```powershell
cd C:\Users\Samuel\MyProjects\AITT\aitt
npm run dev
```

Set this in `aitt/.env.local`:

```bash
AITT_INTERVIEWER_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

## Amplify And AWS Split

For deployment, keep the architecture split:

- `aitt/` can go to Amplify Hosting
- `local-services/interviewer-api/` should stay a separate Python service

If you want AWS hosting for the Python service from the same monorepo, App
Runner is the closest fit because it can deploy a service from a source
directory inside a repository.

Important: the current `local_primary` engine talks to Ollama over
`AITT_OLLAMA_BASE_URL`. Deploying the Python service alone is not enough unless
a reachable Ollama runtime is also available. If not, switch to
`AITT_PRIMARY_ENGINE=nanogpt_backup`.

## Recommended Two-Terminal Workflow

Terminal 1:

```powershell
cd C:\Users\Samuel\MyProjects\AITT
python -m uvicorn app:app --app-dir local-services\interviewer-api --reload --port 8000
```

Terminal 2:

```powershell
cd C:\Users\Samuel\MyProjects\AITT\aitt
npm run dev
```

## Quick Health Verification

After both are running:

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing
Invoke-WebRequest -Uri "http://127.0.0.1:3000/api/interview/health" -UseBasicParsing
```

If both return `200`, the backend and frontend proxy path are wired correctly.

## Common Local Issues

Port `8000` already in use:

```powershell
Get-NetTCPConnection -LocalPort 8000 -State Listen
```

If another local instance is already bound, stop it or change the port and
update `AITT_INTERVIEWER_API_URL`.

Ollama not available:
- check `AITT_OLLAMA_BASE_URL`
- run `ollama list`
- switch to `AITT_PRIMARY_ENGINE=nanogpt_backup` if needed

Stale runtime artifacts:
- `local-services/interviewer-api/runtime/`
- `local-services/interviewer-api/runtime-logs/`

These are disposable and should not be committed.

## Known Operational Reality

The local-primary Ollama path works on this machine, but it is not fast. A live
behavioral turn was observed at roughly 20 seconds after prompt tightening. The
heuristic fallback and the backup Transformer path exist partly to keep the
system usable when the primary local model is slow or unavailable.
