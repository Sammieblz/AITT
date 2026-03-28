import type {
  GenerateTurnResponse,
  InterviewSession,
  StartSessionRequest,
  GenerateTurnRequest,
} from "../interview-types";

export type {
  GenerateTurnResponse,
  InterviewSession,
  StartSessionRequest,
  GenerateTurnRequest,
} from "../interview-types";

export class InterviewerApiError extends Error {
  readonly status: number;
  readonly body: string;

  constructor(status: number, body: string) {
    super(`Interviewer API request failed: ${status} ${body}`);
    this.status = status;
    this.body = body;
  }
}

function requireInterviewerApiBaseUrl() {
  const value =
    process.env.AITT_INTERVIEWER_API_URL ?? process.env.AITT_LOCAL_MODEL_URL;
  if (!value) {
    throw new Error("Missing AITT_INTERVIEWER_API_URL");
  }
  return value.replace(/\/$/, "");
}

export async function requestInterviewerApi<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`${requireInterviewerApiBaseUrl()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new InterviewerApiError(response.status, await response.text());
  }

  return (await response.json()) as T;
}

export async function startInterviewSessionServer(
  payload: StartSessionRequest,
): Promise<InterviewSession> {
  return requestInterviewerApi<InterviewSession>("/session/start", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function generateInterviewTurnServer(
  payload: GenerateTurnRequest,
): Promise<GenerateTurnResponse> {
  return requestInterviewerApi<GenerateTurnResponse>("/generate-turn", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
