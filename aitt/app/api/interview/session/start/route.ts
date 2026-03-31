import { NextResponse } from "next/server";

import {
  InterviewerApiError,
  type InterviewSession,
  requestInterviewerApi,
} from "../../../../../lib/server/interviewer-service";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const payload = await requestInterviewerApi<InterviewSession>("/session/start", {
      method: "POST",
      body: JSON.stringify(body),
    });
    return NextResponse.json(payload);
  } catch (error) {
    if (error instanceof InterviewerApiError) {
      return NextResponse.json({ detail: error.body }, { status: error.status });
    }
    return NextResponse.json({ detail: "Unexpected interviewer API failure" }, { status: 500 });
  }
}
