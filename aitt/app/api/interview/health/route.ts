import { NextResponse } from "next/server";

import {
  InterviewerApiError,
  requestInterviewerApi,
} from "../../../../lib/server/interviewer-service";

export async function GET() {
  try {
    const payload = await requestInterviewerApi("/health");
    return NextResponse.json(payload);
  } catch (error) {
    if (error instanceof InterviewerApiError) {
      return NextResponse.json({ detail: error.body }, { status: error.status });
    }
    return NextResponse.json({ detail: "Unexpected interviewer API failure" }, { status: 500 });
  }
}
