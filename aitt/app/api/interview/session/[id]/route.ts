import { NextResponse } from "next/server";

import {
  InterviewerApiError,
  type InterviewSession,
  requestInterviewerApi,
} from "../../../../../lib/server/interviewer-service";

export async function GET(
  _request: Request,
  context: { params: Promise<{ id: string }> },
) {
  try {
    const params = await context.params;
    const payload = await requestInterviewerApi<InterviewSession>(`/session/${params.id}`);
    return NextResponse.json(payload);
  } catch (error) {
    if (error instanceof InterviewerApiError) {
      return NextResponse.json({ detail: error.body }, { status: error.status });
    }
    return NextResponse.json({ detail: "Unexpected interviewer API failure" }, { status: 500 });
  }
}
