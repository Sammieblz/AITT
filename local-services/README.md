# Local Services

`local-services/` is the backend workspace for deployable services and shared
service contracts.

Current contents:

- [`interviewer-api/`](./interviewer-api): FastAPI behavioral interviewer service
- [`contracts/`](./contracts): shared TypeScript service contracts for backend-to-backend integration

The Next.js app should not call `local_model/` directly. It should proxy through
same-origin route handlers and let those route handlers call the backend
service.

## Design Intent

- `local_model/` stays focused on training, data prep, and owned checkpoints
- `local-services/` owns deployable runtime APIs
- runtime state such as SQLite databases and logs belongs here, not in the
  training workspace
