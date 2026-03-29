'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import ScoreIndicator from '@/components/ScoreIndicator/ScoreIndicator'
import Button from '@/components/Button/Button'
import { useAuth } from '@/lib/AuthContext'
import { startInterviewSession, generateInterviewTurn } from '@/lib/interview-api'
import type { InterviewSession, GenerateTurnResponse, StarScores } from '@/lib/interview-types'
import styles from './page.module.css'

// ── Types ──────────────────────────────────────────────────────────────────
type Phase = 'quiet-notice' | 'mic-check' | 'interview' | 'results'

interface TranscriptLine {
  role: 'ai' | 'user'
  text: string
}

const QUESTION_CATEGORIES = [
  'Leadership',
  'Problem solving',
  'Conflict & collaboration',
  'Achievement & impact',
]

// ── Voice helpers ──────────────────────────────────────────────────────────
async function transcribeAudio(blob: Blob): Promise<string> {
  const form = new FormData()
  form.append('audio', blob, 'audio.webm')
  const res = await fetch('/api/voice/transcribe', { method: 'POST', body: form })
  if (!res.ok) throw new Error(`Transcription failed: ${res.status}`)
  const data = await res.json()
  return data.text ?? ''
}

async function speakText(text: string): Promise<void> {
  console.log('[speak] requesting TTS for:', text.slice(0, 60))
  const res = await fetch('/api/voice/speak', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!res.ok) {
    const err = await res.text()
    console.error('[speak] TTS failed:', res.status, err)
    return
  }
  const audioBlob = await res.blob()
  console.log('[speak] got audio blob, size:', audioBlob.size)
  const url = URL.createObjectURL(audioBlob)
  const audio = new Audio(url)
  await new Promise<void>((resolve) => {
    audio.onended = () => { URL.revokeObjectURL(url); resolve() }
    audio.onerror = (e) => { console.error('[speak] audio playback error:', e); URL.revokeObjectURL(url); resolve() }
    audio.play().catch((e) => { console.error('[speak] audio.play() failed:', e); resolve() })
  })
}

// ── Quiet Notice ───────────────────────────────────────────────────────────
function QuietNotice({ onReady }: { onReady: () => void }) {
  return (
    <div className={styles.phase}>
      <div className={styles.phaseHeader}>
        <h1 className={styles.phaseHeadline}>Find a quiet space</h1>
        <p className={styles.phaseSub}>
          The AI listens carefully to your answers. Background noise can
          interrupt scoring and disrupt the flow of the session.
        </p>
      </div>
      <Button variant="volt" size="lg" onClick={onReady}>
        I&apos;m in a quiet space →
      </Button>
    </div>
  )
}

// ── Mic Check ─────────────────────────────────────────────────────────────
function MicCheck({ onReady }: { onReady: () => void }) {
  const [level, setLevel] = useState(0)
  const [hasPermission, setHasPermission] = useState<boolean | null>(null)
  const [hasSpeaking, setHasSpeaking] = useState(false)
  const rafRef = useRef<number | null>(null)
  const streamRef = useRef<MediaStream | null>(null)

  useEffect(() => {
    let active = true
    async function init() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        if (!active) { stream.getTracks().forEach(t => t.stop()); return }
        streamRef.current = stream
        const ctx = new AudioContext()
        const source = ctx.createMediaStreamSource(stream)
        const analyser = ctx.createAnalyser()
        analyser.fftSize = 256
        source.connect(analyser)
        setHasPermission(true)
        const data = new Uint8Array(analyser.frequencyBinCount)
        function tick() {
          analyser.getByteFrequencyData(data)
          const rms = Math.sqrt(data.reduce((s, v) => s + v * v, 0) / data.length)
          const norm = Math.min(rms / 80, 1)
          setLevel(norm)
          if (norm > 0.15) setHasSpeaking(true)
          rafRef.current = requestAnimationFrame(tick)
        }
        rafRef.current = requestAnimationFrame(tick)
      } catch { setHasPermission(false) }
    }
    init()
    return () => {
      active = false
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
      streamRef.current?.getTracks().forEach(t => t.stop())
    }
  }, [])

  const BAR_COUNT = 5
  return (
    <div className={styles.phase}>
      <div className={styles.phaseHeader}>
        <div className={styles.stepPill}>Step 1 of 3</div>
        <h1 className={styles.phaseHeadline}>Mic check</h1>
        <p className={styles.phaseSub}>Speak a few words — we need to hear you clearly.</p>
      </div>
      {hasPermission === false ? (
        <div className={styles.micError}>
          <p className={styles.micErrorText}>Microphone access denied.</p>
          <p className={styles.micErrorSub}>Allow microphone access in your browser settings and reload.</p>
        </div>
      ) : (
        <>
          <div className={styles.meterWrap} aria-label="Audio level meter">
            {Array.from({ length: BAR_COUNT }).map((_, i) => (
              <span
                key={i}
                className={[styles.meterBar, level >= ((i + 1) / BAR_COUNT) * 0.6 ? styles.meterBarActive : ''].join(' ')}
                style={{ height: `${20 + i * 10}px` }}
              />
            ))}
          </div>
          <p className={styles.micStatus}>
            {hasPermission === null ? 'Requesting mic access…' : hasSpeaking ? '✓ We can hear you' : 'Say something to test your mic'}
          </p>
          <Button variant="volt" size="lg" disabled={!hasSpeaking} onClick={onReady}>
            Mic sounds good →
          </Button>
        </>
      )}
    </div>
  )
}

// ── Interview ──────────────────────────────────────────────────────────────
function Interview({ onComplete }: { onComplete: (scores: StarScores[], questions: string[]) => void }) {
  const [session, setSession] = useState<InterviewSession | null>(null)
  const [transcript, setTranscript] = useState<TranscriptLine[]>([])
  const [allScores, setAllScores] = useState<StarScores[]>([])
  const [questions, setQuestions] = useState<string[]>([])
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [started, setStarted] = useState(false)
  const [isMuted, setIsMuted] = useState(false)

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const transcriptEndRef = useRef<HTMLDivElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const stopRecordingRef = useRef<(() => void) | null>(null)
  const vadRafRef = useRef<number | null>(null)
  const silenceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const hasSpokeRef = useRef(false)
  const isMutedRef = useRef(false)

  const SILENCE_THRESHOLD = 0.08
  const SILENCE_DURATION  = 1800

  useEffect(() => { isMutedRef.current = isMuted }, [isMuted])

  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [transcript])

  // Start session and get first question
  const startSession = useCallback(async () => {
    try {
      setError(null)
      console.log('[session] starting session...')
      const s = await startInterviewSession({ mode: 'behavioral', level: 'intern' })
      console.log('[session] started:', s.session_id, 'question:', s.question)
      setSession(s)
      setStarted(true)
      const q = s.question ?? 'Tell me about a time you led a team through a difficult challenge.'
      setQuestions([q])
      setTranscript([{ role: 'ai', text: q }])
      setIsSpeaking(true)
      await speakText(q)
      setIsSpeaking(false)
    } catch (e) {
      console.error('[session] startSession error:', e)
      setError(`Failed to start session: ${String(e)}`)
    }
  }, [])

  // Start recording with VAD auto-stop
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      const ctx = new AudioContext()
      const source = ctx.createMediaStreamSource(stream)
      const analyser = ctx.createAnalyser()
      analyser.fftSize = 256
      source.connect(analyser)
      hasSpokeRef.current = false

      const mr = new MediaRecorder(stream, { mimeType: 'audio/webm' })
      chunksRef.current = []
      mr.ondataavailable = (e) => { if (e.data.size > 0) chunksRef.current.push(e.data) }
      mr.start()
      mediaRecorderRef.current = mr
      setIsRecording(true)

      // VAD loop — auto-stop after silence following speech
      const data = new Uint8Array(analyser.frequencyBinCount)
      function vadTick() {
        analyser.getByteFrequencyData(data)
        const rms = Math.sqrt(data.reduce((s, v) => s + v * v, 0) / data.length) / 128
        if (rms > SILENCE_THRESHOLD) {
          hasSpokeRef.current = true
          if (silenceTimerRef.current) { clearTimeout(silenceTimerRef.current); silenceTimerRef.current = null }
        } else if (hasSpokeRef.current && !silenceTimerRef.current) {
          silenceTimerRef.current = setTimeout(() => {
            if (mediaRecorderRef.current?.state === 'recording') {
              stopRecordingRef.current?.()
            }
          }, SILENCE_DURATION)
        }
        vadRafRef.current = requestAnimationFrame(vadTick)
      }
      vadRafRef.current = requestAnimationFrame(vadTick)
    } catch {
      setError('Could not access microphone.')
    }
  }, [])

  // Stop recording, transcribe, send to backend, speak response
  const stopRecording = useCallback(async () => {
    // Clean up VAD
    if (vadRafRef.current) { cancelAnimationFrame(vadRafRef.current); vadRafRef.current = null }
    if (silenceTimerRef.current) { clearTimeout(silenceTimerRef.current); silenceTimerRef.current = null }

    const mr = mediaRecorderRef.current
    if (!mr || mr.state !== 'recording') return
    setIsRecording(false)

    await new Promise<void>((resolve) => {
      mr.onstop = () => resolve()
      mr.stop()
    })
    streamRef.current?.getTracks().forEach(t => t.stop())

    const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' })
    setIsProcessing(true)

    try {
      // 1. Transcribe
      const transcript_text = await transcribeAudio(audioBlob)
      if (transcript_text) {
        setTranscript(prev => [...prev, { role: 'user', text: transcript_text }])
      }

      // 2. Send to AITT backend
      const currentQuestion = questions[questions.length - 1] ?? ''
      const sess = session
      if (!sess) return
      const turn: GenerateTurnResponse = await generateInterviewTurn({
        candidate_answer: transcript_text || '(no answer)',
        session_id: sess.session_id,
        question: currentQuestion,
        group: sess.group as never,
        level: sess.level,
      })

      // 3. Collect scores
      const nextScores = [...allScores, turn.scores]
      setAllScores(nextScores)

      // 4. Show and speak interviewer feedback
      if (turn.interviewer_text) {
        setTranscript(prev => [...prev, { role: 'ai', text: turn.interviewer_text }])
      }

      // 5. If done, finish
      if (nextScores.length >= MAX_QUESTIONS) {
        if (turn.interviewer_text) {
          setIsSpeaking(true)
          await speakText(turn.interviewer_text)
          setIsSpeaking(false)
        }
        setIsProcessing(false)
        onComplete(nextScores, questions)
        return
      }

      // 6. Show and speak follow-up question
      const nextQ = turn.follow_up_question || currentQuestion
      setQuestions(prev => [...prev, nextQ])
      if (nextQ && nextQ !== turn.interviewer_text) {
        setTranscript(prev => [...prev, { role: 'ai', text: nextQ }])
      }

      // 7. Speak feedback, then question
      setIsSpeaking(true)
      if (turn.interviewer_text) {
        await speakText(turn.interviewer_text)
      }
      if (nextQ && nextQ !== turn.interviewer_text) {
        await speakText(nextQ)
      }
      setIsSpeaking(false)
    } catch (e) {
      setError(`Error processing answer: ${String(e)}`)
    } finally {
      setIsProcessing(false)
    }
  }, [session, questions, allScores, isMuted, onComplete])

  // Keep stopRecordingRef in sync
  useEffect(() => { stopRecordingRef.current = stopRecording }, [stopRecording])

  const MAX_QUESTIONS = 4
  const questionNumber = allScores.length

  return (
    <div className={styles.phase}>
      <div className={styles.phaseHeader}>
        <div className={styles.stepPill}>Step 2 of 3</div>
        <h1 className={styles.phaseHeadline}>Mock interview</h1>
        <p className={styles.phaseSub}>
          {!started ? "Press Start when you're ready" :
            isSpeaking ? 'Alex is speaking…' :
            isProcessing ? 'Processing your answer…' :
            isRecording ? 'Recording — press Stop when done' :
            'Press Record to answer'}
        </p>
      </div>

      {/* Question progress */}
      <div className={styles.questionProgress}>
        {Array.from({ length: MAX_QUESTIONS }).map((_, i) => (
          <div key={i} className={styles.questionItem}>
            <div className={[
              styles.questionDot,
              i < questionNumber ? styles.questionDotDone : '',
              i === questionNumber && started ? styles.questionDotActive : '',
            ].filter(Boolean).join(' ')}>{i + 1}</div>
            <span className={styles.questionLabel}>Q{i + 1}</span>
            {allScores[i] && <ScoreIndicator score={Math.round((allScores[i].situation + allScores[i].task + allScores[i].action + allScores[i].result) / 4) as 1|2|3|4|5} />}
          </div>
        ))}
      </div>

      {/* Status */}
      <div className={styles.statusRow}>
        <span className={[styles.statusDot, started ? styles.statusDotLive : ''].join(' ')} />
        <span className={styles.statusText}>
          {!started ? 'Ready' : isRecording ? 'Recording' : isSpeaking ? 'Speaking' : isProcessing ? 'Processing' : 'Live'}
        </span>
        {started && (
          <span className={[styles.speakingIndicator, isMuted ? styles.speakingIndicatorMuted : ''].filter(Boolean).join(' ')}>
            {isSpeaking ? '🔊 Alex' : isMuted ? '🔇 Muted' : isRecording ? '🎙 You' : ''}
          </span>
        )}
      </div>

      {/* Transcript */}
      <div className={styles.transcriptWrap}>
        <div className={styles.transcript}>
          {transcript.length === 0 && (
            <p className={styles.transcriptEmpty}>Transcript will appear here…</p>
          )}
          {transcript.map((line, i) => (
            <p key={i} className={line.role === 'ai' ? styles.lineAi : styles.lineUser}>
              <span className={styles.lineRole}>{line.role === 'ai' ? 'Alex' : 'You'}</span>
              {line.text}
            </p>
          ))}
          <div ref={transcriptEndRef} />
        </div>
        {started && (
          <button
            className={[styles.muteFab, isMuted ? styles.muteFabMuted : ''].filter(Boolean).join(' ')}
            onClick={() => {
              setIsMuted(m => !m)
              // If recording and currently unmuted, treat mute as "done speaking" — stop and submit
              if (isRecording && !isMuted) {
                stopRecordingRef.current?.()
              }
            }}
            aria-label={isMuted ? 'Unmute microphone' : 'Mute microphone'}
          >
            {isMuted ? '🎙 Unmute' : '🔇 Mute'}
          </button>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className={styles.micError}>
          <p className={styles.micErrorText}>Something went wrong</p>
          <p className={styles.micErrorSub}>{error}</p>
        </div>
      )}

      {/* Controls */}
      <div className={styles.controls}>
        {!started && (
          <Button variant="volt" size="lg" onClick={startSession}>
            Start interview →
          </Button>
        )}
        {started && !isRecording && !isProcessing && !isSpeaking && (
          <Button variant="volt" size="lg" onClick={startRecording}>
            🎙 Record answer
          </Button>
        )}
        {isRecording && (
          <Button variant="outline" size="md" onClick={stopRecording}>
            ⏹ Stop recording
          </Button>
        )}
      </div>
    </div>
  )
}

// ── Results ────────────────────────────────────────────────────────────────
function Results({ scores, questions }: { scores: StarScores[], questions: string[] }) {
  const avg = scores.length > 0
    ? (scores.reduce((s, v) => s + (v.situation + v.task + v.action + v.result) / 4, 0) / scores.length).toFixed(1)
    : '—'

  return (
    <div className={styles.phase}>
      <div className={styles.phaseHeader}>
        <div className={styles.stepPill}>Step 3 of 3</div>
        <h1 className={styles.phaseHeadline}>Session complete</h1>
        <p className={styles.phaseSub}>Here's how you scored on the STAR framework.</p>
      </div>

      <div className={styles.resultsGrid}>
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className={styles.resultRow}>
            <div className={styles.resultLeft}>
              <span className={styles.resultQNum}>Q{i + 1}</span>
              <p className={styles.resultQuestion}>{questions[i] ?? QUESTION_CATEGORIES[i]}</p>
            </div>
            {scores[i] ? (
              <ScoreIndicator score={Math.round((scores[i].situation + scores[i].task + scores[i].action + scores[i].result) / 4) as 1|2|3|4|5} />
            ) : (
              <div className={styles.resultScoreMissing}>—</div>
            )}
          </div>
        ))}
      </div>

      <div className={styles.avgRow}>
        <span className={styles.avgLabel}>Average STAR score</span>
        <span className={styles.avgValue}>{avg} / 5</span>
      </div>

      <Button variant="volt" size="lg" href="/dashboard">
        Back to dashboard →
      </Button>
    </div>
  )
}

// ── Page ───────────────────────────────────────────────────────────────────
export default function SessionPage() {
  const { user } = useAuth()
  const [phase, setPhase] = useState<Phase>('quiet-notice')
  const [scores, setScores] = useState<StarScores[]>([])
  const [questions, setQuestions] = useState<string[]>([])
  const interviewStartRef = useRef<Date | null>(null)

  useEffect(() => {
    if (phase === 'interview') interviewStartRef.current = new Date()
  }, [phase])

  async function handleComplete(s: StarScores[], qs: string[]) {
    setScores(s)
    setQuestions(qs)
    setPhase('results')
    if (!user) return
    const durationMinutes = interviewStartRef.current
      ? Math.round((Date.now() - interviewStartRef.current.getTime()) / 60000)
      : 0
    const avgScores = s.map(v => Math.round((v.situation + v.task + v.action + v.result) / 4))
    await fetch('/api/sessions', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ userId: user.userId, scores: avgScores, durationMinutes, categories: QUESTION_CATEGORIES }),
    })
  }

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <Link href="/dashboard" className={styles.wordmark}>
          <span className={styles.wordmarkVoid}>interview</span>
          <span className={styles.wordmarkVolt}>AI</span>
        </Link>
        <div className={styles.headerRight}>
          {(['mic-check', 'interview', 'results'] as Phase[]).map((p) => (
            <div key={p} className={[
              styles.phasePip,
              phase === p ? styles.phasePipActive : (['interview', 'results'].includes(phase) && p === 'mic-check') || (phase === 'results' && p === 'interview') ? styles.phasePipDone : '',
            ].filter(Boolean).join(' ')} />
          ))}
        </div>
      </header>

      <main className={styles.main}>
        {phase === 'quiet-notice' && <QuietNotice onReady={() => setPhase('mic-check')} />}
        {phase === 'mic-check' && <MicCheck onReady={() => setPhase('interview')} />}
        {phase === 'interview' && <Interview onComplete={handleComplete} />}
        {phase === 'results' && <Results scores={scores} questions={questions} />}
      </main>
    </div>
  )
}
