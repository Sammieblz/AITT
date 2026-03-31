# API And Next.js Integration

## Integration Rule

The browser should treat the Next.js app as the only backend contract for
behavioral interviews.

The browser should not:

- read SQLite directly
- read dataset JSON files directly
- call the interviewer Python service URL directly

## Base URL

Set in:

- `aitt/.env.local`

Value:

```bash
AITT_INTERVIEWER_API_URL=http://127.0.0.1:8000
```

If you deploy the Next.js app, set `AITT_INTERVIEWER_API_URL` to the public URL
of the Python service. It should not point to `localhost` in hosted
environments.

## Same-Origin Browser Routes

The browser should call:

- `POST /api/interview/session/start`
- `POST /api/interview/turn`
- `GET /api/interview/session/{id}`
- `GET /api/interview/health`

These routes proxy the Python service and keep service env vars server-side.

## Current Boundary

Browser:
- calls same-origin Next routes only

Next app server:
- reads `AITT_INTERVIEWER_API_URL`
- proxies requests to `local-services/interviewer-api`

Interviewer service:
- reads source data from `local_model/data/behavioral_interview/`
- persists runtime state under `local-services/interviewer-api/runtime/`

## Python Service Routes

The Next routes proxy:

- `POST /session/start`
- `POST /generate-turn`
- `GET /session/{id}`
- `GET /health`

## Contract Placement

Shared backend contract definitions live in:

- [`../local-services/contracts/interviewer.ts`](../local-services/contracts/interviewer.ts)

The current Next app uses these local files for runtime stability:

- [`../aitt/lib/interview-types.ts`](../aitt/lib/interview-types.ts)
- [`../aitt/lib/server/interviewer-service.ts`](../aitt/lib/server/interviewer-service.ts)
- [`../aitt/lib/interview-api.ts`](../aitt/lib/interview-api.ts)

This keeps `local-services/` as the backend workspace while avoiding Next
dev/build issues with cross-workspace package resolution.

## Main Response Shape

The proxy preserves the current service payload:

- `engine`
- `session_id`
- `question_id`
- `question`
- `group`
- `tags`
- `candidate_answer`
- `interviewer_text`
- `follow_up_question`
- `follow_up_intent`
- `scores`
- `feedback`
- `confidence`

## Current Implementation Locations

Browser-side helper:

- [`../aitt/lib/interview-api.ts`](../aitt/lib/interview-api.ts)

Next server-side proxy:

- [`../aitt/lib/server/interviewer-service.ts`](../aitt/lib/server/interviewer-service.ts)

Next route handlers:

- `aitt/app/api/interview/...`

## Minimal App Flow

1. Call `startInterviewSession`
2. Render the opening `question`
3. Collect the user answer
4. Call `generateInterviewTurn`
5. Display:
   - `interviewer_text`
   - `follow_up_question`
   - STAR `scores`
   - `feedback`
6. Optionally re-fetch the session with `getInterviewSession`

## Voice Layer Compatibility

The voice layer should:

1. capture audio
2. transcribe it externally
3. send the transcript as `candidate_answer`
4. read back `interviewer_text`
5. optionally speak `follow_up_question` as the next prompt

This keeps the interviewer service text-only and voice decoupled.

## Amplify Deployment Note

Amplify is a good fit for the `aitt/` shell, but not for the current
`local-services/interviewer-api/` runtime.

Current version note: `aitt/package.json` is pinned to Next `16.2.1`. The AWS
Amplify Hosting docs currently describe support for Next.js `12` through `15`,
so the app should be downgraded to a supported Next version before treating
Amplify as the default host.

The practical deployment split is:

- `aitt/` on Amplify Hosting
- `local-services/interviewer-api/` on separate compute, such as AWS App Runner

For this repo's monorepo layout, Amplify should be pointed at the app root:

```bash
AMPLIFY_MONOREPO_APP_ROOT=aitt
```

The frontend env it needs is:

```bash
AITT_INTERVIEWER_API_URL=https://<your-interviewer-service-url>
NEXT_PUBLIC_APP_URL=https://<your-frontend-url>
```
