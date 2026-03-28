## AITT App

This is the Next.js shell for AITT.

Full documentation lives in:

- [`../docs/README.md`](../docs/README.md)
- [`../docs/api-and-nextjs-integration.md`](../docs/api-and-nextjs-integration.md)
- [`../docs/environment-reference.md`](../docs/environment-reference.md)
- [`../docs/repo-hygiene.md`](../docs/repo-hygiene.md)

## Getting Started

Install dependencies and run the app:

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Interviewer Backend Integration

The browser should talk only to same-origin Next API routes. Those route
handlers call the interviewer backend service over HTTP. Do not read dataset
files or SQLite directly from the app.

Set this in `aitt/.env.local`:

```bash
AITT_INTERVIEWER_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

Use the thin app helper in [lib/interview-api.ts](./lib/interview-api.ts):

```ts
import {
  generateInterviewTurn,
  getInterviewSession,
  startInterviewSession,
} from "@/lib/interview-api";

const session = await startInterviewSession({
  group: "Leadership & Influence",
  level: "intern",
});

const turn = await generateInterviewTurn({
  session_id: session.session_id,
  candidate_answer: "During my internship...",
});

const hydratedSession = await getInterviewSession(session.session_id);
```

Server-side proxying to the interviewer backend lives in:

- [`lib/server/interviewer-service.ts`](./lib/server/interviewer-service.ts)
- [`lib/interview-types.ts`](./lib/interview-types.ts)

## What The App Should Not Own

- direct database access
- direct filesystem reads into `local_model/`
- direct browser calls to the Python service URL
- Ollama or model orchestration logic

Current same-origin endpoints expected by the app:

- `POST /api/interview/session/start`
- `POST /api/interview/turn`
- `GET /api/interview/session/{id}`
- `GET /api/interview/health`
