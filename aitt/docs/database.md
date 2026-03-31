# Database Architecture

AITT uses AWS DynamoDB for all persistence. There are two tables.

---

## Tables

### `aitt-users`

Stores user profile data written during the setup flow (`/setup`) and updated via the profile edit modal on the dashboard.

| Attribute | Type | Role |
|-----------|------|------|
| `userId` | String | **Partition key** — Cognito `sub` claim from the ID token |
| `name` | String | Display name (from Cognito `name` attribute) |
| `targetRole` | String | e.g. "Software Engineer" |
| `targetCompany` | String | e.g. "Google" |
| `level` | String | "Entry", "Mid", "Senior", or "Staff+" |
| `focusAreas` | String[] | Subset of: Leadership, Problem solving, Conflict & collaboration, Achievement & impact |
| `memberSince` | String | ISO date string set at profile creation |
| `upcomingInterview` | Object? | Optional — `{ company, role, date, round }` |

Billing: PAY_PER_REQUEST (on-demand).

### `aitt-sessions`

Stores individual interview session results, written immediately after the AI session ends.

| Attribute | Type | Role |
|-----------|------|------|
| `userId` | String | **Partition key** — matches `aitt-users` |
| `sessionId` | String | **Sort key** — `crypto.randomUUID()` |
| `date` | String | ISO date (YYYY-MM-DD) |
| `score` | Number | Average of `scores` array, rounded to 1 decimal |
| `scores` | Number[] | Per-question STAR scores (1–5), one per question |
| `durationMinutes` | Number | Wall-clock time from session start to end |
| `categories` | String[] | Question categories answered in this session |
| `topInsight` | String | Auto-generated feedback string based on score range |

Billing: PAY_PER_REQUEST (on-demand).

> **Key naming matters.** The sort key must be `sessionId` (camelCase). If you recreate this table via the AWS Console it may default to `session_id` — use the CLI or double-check the key name before saving.

---

## AWS Setup

### Creating the tables (CLI)

```bash
# aitt-users
aws dynamodb create-table \
  --table-name aitt-users \
  --attribute-definitions AttributeName=userId,AttributeType=S \
  --key-schema AttributeName=userId,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1

# aitt-sessions
aws dynamodb create-table \
  --table-name aitt-sessions \
  --attribute-definitions \
      AttributeName=userId,AttributeType=S \
      AttributeName=sessionId,AttributeType=S \
  --key-schema \
      AttributeName=userId,KeyType=HASH \
      AttributeName=sessionId,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

Wait for `ACTIVE` status:

```bash
aws dynamodb wait table-exists --table-name aitt-users --region us-east-1
aws dynamodb wait table-exists --table-name aitt-sessions --region us-east-1
```

### Required environment variables

Add these to `.env.local` (never commit this file):

```
AWS_DEFAULT_REGION="us-east-1"
AWS_ACCESS_KEY_ID="..."
AWS_SECRET_ACCESS_KEY="..."
# Only needed if using temporary STS credentials (e.g. workshop/federated accounts)
AWS_SESSION_TOKEN="..."
```

The Next.js API routes read credentials from the environment at runtime via the AWS SDK default credential provider chain. No additional configuration is needed.

> **Temporary credentials** (keys starting with `ASIA`) expire — typically within a few hours. If you see 500 errors from `/api/user` or `/api/sessions`, your credentials have likely expired. Refresh them from your AWS account portal and restart the dev server.

---

## Server integration

All DynamoDB access goes through Next.js API route handlers. Client components never call DynamoDB directly.

```
Client Component
    ↓ fetch()
API Route Handler (app/api/*/route.ts)   ← server-only
    ↓ DynamoDBDocumentClient
DynamoDB
```

### `lib/dynamodb.ts`

Singleton document client. Import only in API routes (server-only).

```ts
import { DynamoDBClient } from '@aws-sdk/client-dynamodb'
import { DynamoDBDocumentClient } from '@aws-sdk/lib-dynamodb'

const client = new DynamoDBClient({ region: process.env.AWS_DEFAULT_REGION ?? 'us-east-1' })
export const ddb = DynamoDBDocumentClient.from(client)
```

### `app/api/user/route.ts`

| Method | Description |
|--------|-------------|
| `GET ?userId=xxx` | Fetch a user profile. Returns 404 if not found (used to detect first login). |
| `PUT { userId, ...fields }` | Create or overwrite a user profile (full replace — include all fields). |

### `app/api/sessions/route.ts`

| Method | Description |
|--------|-------------|
| `GET ?userId=xxx` | Fetch up to 50 sessions for a user, newest first. |
| `POST { userId, scores, durationMinutes, categories }` | Write a new session. Computes `score` (avg) and `topInsight` server-side. |

---

## Extending the schema

DynamoDB is schema-less — you can add new attributes to any item without a migration. A few conventions to follow:

- **New user profile fields**: add them to the `PUT /api/user` body and the `UserProfile` interface in `app/dashboard/page.tsx`. The existing `PutCommand` will include them automatically (full-replace write).
- **New session fields**: add them to the `POST /api/sessions` body and the `RawSession` type in `lib/dashboardCompute.ts`. Old sessions won't have the field — guard with `session.field ?? defaultValue`.
- **New tables**: create with PAY_PER_REQUEST billing, add the table name as a constant at the top of the route file (see the `TABLE` constant pattern), and create a new route handler under `app/api/`.
- **Indexes (GSI)**: if you need to query sessions by date across all users, add a GSI with `date` as the partition key. Define it in the `create-table` CLI call or add via `update-table`.

---

## Auth connection

`userId` in both tables is always the Cognito `sub` claim — a stable UUID assigned at user creation that never changes, even if the user's email changes. It is decoded client-side from the Cognito ID token stored in localStorage by `lib/auth.ts` and passed to all API calls.
