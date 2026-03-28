import type {
  GenerateTurnResponse,
  InterviewSession,
  StartSessionRequest,
  GenerateTurnRequest,
} from "./interview-types";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Interview API request failed: ${response.status} ${await response.text()}`);
  }

  return (await response.json()) as T;
}

export async function startInterviewSession(
  request: StartSessionRequest = {},
): Promise<InterviewSession> {
  return requestJson<InterviewSession>("/api/interview/session/start", {
    method: "POST",
    body: JSON.stringify({
      mode: request.mode ?? "behavioral",
      group: request.group ?? "Leadership & Influence",
      level: request.level ?? "intern",
      question_id: request.question_id ?? null,
      question: request.question ?? null,
      metadata: request.metadata ?? {},
    }),
  });
}

export async function generateInterviewTurn(
  request: GenerateTurnRequest,
): Promise<GenerateTurnResponse> {
  return requestJson<GenerateTurnResponse>("/api/interview/turn", {
    method: "POST",
    body: JSON.stringify(request),
  });
}

export async function getInterviewSession(
  sessionId: string,
): Promise<InterviewSession> {
  return requestJson<InterviewSession>(`/api/interview/session/${sessionId}`);
}

export async function getInterviewHealth(): Promise<unknown> {
  return requestJson("/api/interview/health");
}
