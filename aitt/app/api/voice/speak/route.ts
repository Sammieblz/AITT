import { NextResponse } from "next/server";

// POST /api/voice/speak
// Accepts: { text: string, voice_id?: string }
// Returns: audio/mpeg binary stream
export async function POST(request: Request) {
  const apiKey = process.env.ELEVENLABS_API_KEY ?? process.env.NEXT_PUBLIC_ELEVENLABS_API_KEY;
  if (!apiKey) {
    return NextResponse.json({ detail: "Missing ElevenLabs API key" }, { status: 500 });
  }

  try {
    const { text, voice_id } = await request.json();
    if (!text) {
      return NextResponse.json({ detail: "Missing text" }, { status: 400 });
    }

    // Default to the "James" voice used in the original agent config
    const voiceId = voice_id ?? process.env.ELEVENLABS_VOICE_ID ?? "TX3LPaxmHKxFdv7VOQHJ";

    const res = await fetch(
      `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}/stream`,
      {
        method: "POST",
        headers: {
          "xi-api-key": apiKey,
          "Content-Type": "application/json",
          Accept: "audio/mpeg",
        },
        body: JSON.stringify({
          text,
          model_id: "eleven_turbo_v2_5",
          voice_settings: { stability: 0.57, similarity_boost: 0.39, speed: 0.87 },
        }),
      },
    );

    if (!res.ok) {
      const err = await res.text();
      return NextResponse.json({ detail: err }, { status: res.status });
    }

    const audioBuffer = await res.arrayBuffer();
    return new NextResponse(audioBuffer, {
      headers: {
        "Content-Type": "audio/mpeg",
        "Cache-Control": "no-store",
      },
    });
  } catch (e) {
    return NextResponse.json({ detail: String(e) }, { status: 500 });
  }
}
