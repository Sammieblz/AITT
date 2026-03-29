import { NextResponse } from "next/server";

// POST /api/voice/transcribe
// Accepts: multipart/form-data with an "audio" file field
// Returns: { text: string }
export async function POST(request: Request) {
  const apiKey = process.env.ELEVENLABS_API_KEY ?? process.env.NEXT_PUBLIC_ELEVENLABS_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ detail: "Missing ElevenLabs API key" }, { status: 500 });
  }

  try {
    const formData = await request.formData();
    const audio = formData.get("audio");
    if (!audio || !(audio instanceof Blob)) {
      return NextResponse.json({ detail: "Missing audio field" }, { status: 400 });
    }

    const body = new FormData();
    body.append("file", audio, "audio.webm");
    body.append("model_id", "scribe_v1");

    const res = await fetch("https://api.elevenlabs.io/v1/speech-to-text", {
      method: "POST",
      headers: { "xi-api-key": apiKey },
      body,
    });

    if (!res.ok) {
      const err = await res.text();
      return NextResponse.json({ detail: err }, { status: res.status });
    }

    const data = await res.json();
    // ElevenLabs STT returns { text: string, ... }
    return NextResponse.json({ text: data.text ?? "" });
  } catch (e) {
    return NextResponse.json({ detail: String(e) }, { status: 500 });
  }
}
