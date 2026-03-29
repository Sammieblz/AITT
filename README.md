# AITT

AITT is a behavioral interview training system for computer science students.

The repo is split into three workspaces:

- [`aitt/`](./aitt): the Next.js app shell
- [`local_model/`](./local_model): training, dataset generation, and owned Transformer checkpoints
- [`local-services/`](./local-services): deployable backend services and shared service contracts

## Quick Start

1. Prepare the local model workspace:

```powershell
cd C:\Users\Samuel\MyProjects\AITT\local_model
pip install -r requirements.txt
python data\behavioral_interview\prepare.py
```

2. Start the interviewer API:

```powershell
cd C:\Users\Samuel\MyProjects\AITT
pip install -r local-services\interviewer-api\requirements.txt
python -m uvicorn app:app --app-dir local-services\interviewer-api --reload --port 8000
```

3. Start the Next.js app:

```powershell
cd C:\Users\Samuel\MyProjects\AITT\aitt
npm install
npm run dev
```

4. Set `aitt/.env.local`:

```bash
AITT_INTERVIEWER_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

## Architecture Summary

The interviewer runtime is hybrid:

- `local_primary`: Ollama-backed local instruct model
- `nanogpt_backup`: owned decoder-only Transformer fine-tune in `local_model`
- `heuristic_dev`: deterministic fallback for development and tests

The browser never calls the Python service directly. It talks to same-origin
Next API routes, and those route handlers proxy the backend service in
`local-services/interviewer-api`.

## Documentation

Start here:

- [`docs/README.md`](./docs/README.md)
- [`docs/local-model-architecture.md`](./docs/local-model-architecture.md)
- [`docs/local-model-runbook.md`](./docs/local-model-runbook.md)
- [`docs/data-and-storage.md`](./docs/data-and-storage.md)
- [`docs/api-and-nextjs-integration.md`](./docs/api-and-nextjs-integration.md)
- [`docs/environment-reference.md`](./docs/environment-reference.md)
- [`docs/repo-hygiene.md`](./docs/repo-hygiene.md)
