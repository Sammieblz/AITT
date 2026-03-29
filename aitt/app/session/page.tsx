'use client'

import { useConversation } from '@elevenlabs/react'
import { useCallback, useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import ScoreIndicator from '@/components/ScoreIndicator/ScoreIndicator'
import Button from '@/components/Button/Button'
import styles from './page.module.css'

// ── Types ──────────────────────────────────────────────────────────────────
type Phase = 'quiet-notice' | 'mic-check' | 'interview' | 'results'
type Score = 1 | 2 | 3 | 4 | 5

interface TranscriptLine {
  role: 'ai' | 'user'
  text: string
}

const QUESTIONS = [
  'Tell me about a time you led a team through a difficult challenge.',
  'Describe a situation where you had to solve a complex technical problem with limited information.',
  'Tell me about a time you failed and what you learned.',
  'What has been your most impactful achievement and how did you measure it?',
]

function extractScore(text: string): Score | null {
  const m =
    /STAR\s+[Ss]core[^.]{0,30}([1-5])\s*\/\s*5/i.exec(text) ??
    /\b([1-5])\s*\/\s*5/i.exec(text) ??
    /\b([1-5])\s+out\s+of\s+5/i.exec(text)
  return m ? (parseInt(m[1], 10) as Score) : null
}

// ── Quiet Notice ───────────────────────────────────────────────────────────
function QuietNotice({ onReady }: { onReady: () => void }) {
  return (
    <div className={styles.phase}>
      <div className={styles.phaseHeader}>
        <h1 className={styles.phaseHeadline}>Find a quiet space</h1>
        <p className={styles.phaseSub}>
          The AI listens carefully to your answers. Background noise can
          interrupt scoring and disrupt the flow of the session. Take a moment
          to find somewhere you won't be disturbed.
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
  const analyserRef = useRef<AnalyserNode | null>(null)
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
        analyserRef.current = analyser
        setHasPermission(true)

        const data = new Uint8Array(analyser.frequencyBinCount)
        function tick() {
          analyser.getByteFrequencyData(data)
          const rms = Math.sqrt(data.reduce((sum, v) => sum + v * v, 0) / data.length)
          const norm = Math.min(rms / 80, 1)
          setLevel(norm)
          if (norm > 0.15) setHasSpeaking(true)
          rafRef.current = requestAnimationFrame(tick)
        }
        rafRef.current = requestAnimationFrame(tick)
      } catch {
        setHasPermission(false)
      }
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
          <p className={styles.micErrorSub}>
            Allow microphone access in your browser settings and reload the page.
          </p>
        </div>
      ) : (
        <>
          <div className={styles.meterWrap} aria-label="Audio level meter">
            {Array.from({ length: BAR_COUNT }).map((_, i) => {
              const threshold = (i + 1) / BAR_COUNT
              const active = level >= threshold * 0.6
              return (
                <span
                  key={i}
                  className={[styles.meterBar, active ? styles.meterBarActive : ''].join(' ')}
                  style={{ height: `${20 + i * 10}px` }}
                />
              )
            })}
          </div>

          <p className={styles.micStatus}>
            {hasPermission === null
              ? 'Requesting mic access…'
              : hasSpeaking
              ? '✓ We can hear you'
              : 'Say something to test your mic'}
          </p>

          <Button
            variant="volt"
            size="lg"
            disabled={!hasSpeaking}
            onClick={onReady}
          >
            Mic sounds good →
          </Button>
        </>
      )}
    </div>
  )
}

// ── Interview ──────────────────────────────────────────────────────────────
function Interview({ onComplete }: { onComplete: (scores: Score[]) => void }) {
  const [transcript, setTranscript] = useState<TranscriptLine[]>([])
  const [scores, setScores] = useState<Score[]>([])
  const [questionNumber, setQuestionNumber] = useState(0)
  const [connError, setConnError] = useState<string | null>(null)
  const [isMuted, setIsMuted] = useState(false)
  const transcriptEndRef = useRef<HTMLDivElement>(null)
  const scoresRef = useRef<Score[]>([])
  // True once the agent sends its first message — session is real, not a dropped connection
  const sessionStartedRef = useRef(false)

  const conversation = useConversation({
    micMuted: isMuted,
    onConnect: () => console.log('[ElevenLabs] connected'),
    onDisconnect: () => {
      console.log('[ElevenLabs] disconnected')
      if (!sessionStartedRef.current) {
        setConnError('Connection dropped before the interview started. Please try again.')
        return
      }
      onComplete(scoresRef.current)
    },
    onError: (err) => {
      console.error('[ElevenLabs] error:', err)
      setConnError('Connection error. Please try again.')
    },
    onMessage: (message) => {
      const role = message.source === 'ai' ? 'ai' : 'user'
      const text = message.message ?? ''

      // Mark session as real once the agent speaks
      if (role === 'ai') sessionStartedRef.current = true

      setTranscript(prev => [...prev, { role, text }])

      if (role === 'ai') {
        const score = extractScore(text)
        if (score !== null) {
          const next = [...scoresRef.current, score]
          scoresRef.current = next
          setScores(next)
          setQuestionNumber(next.length)
          if (next.length >= 4) {
            setTimeout(() => conversation.endSession(), 3000)
          }
        }
      }
    },
  })

  const start = useCallback(async () => {
    await conversation.startSession({
      agentId: process.env.NEXT_PUBLIC_ELEVENLABS_AGENT_ID!,
      connectionType: 'webrtc',
    })
  }, [conversation])

  const stop = useCallback(async () => {
    await conversation.endSession()
  }, [conversation])

  // Scroll transcript to bottom on update
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [transcript])

  const isConnected = conversation.status === 'connected'

  return (
    <div className={styles.phase}>
      <div className={styles.phaseHeader}>
        <div className={styles.stepPill}>Step 2 of 3</div>
        <h1 className={styles.phaseHeadline}>Mock interview</h1>
        <p className={styles.phaseSub}>
          {isConnected
            ? conversation.isSpeaking
              ? 'Alex is speaking…'
              : 'Your turn — answer naturally'
            : 'Press Start when you\'re ready'}
        </p>
      </div>

      {/* Question progress */}
      <div className={styles.questionProgress}>
        {QUESTIONS.map((q, i) => (
          <div key={i} className={styles.questionItem}>
            <div
              className={[
                styles.questionDot,
                i < questionNumber ? styles.questionDotDone : '',
                i === questionNumber && isConnected ? styles.questionDotActive : '',
              ].filter(Boolean).join(' ')}
            >
              {i + 1}
            </div>
            <span className={styles.questionLabel}>Q{i + 1}</span>
            {scores[i] && (
              <ScoreIndicator score={scores[i]} />
            )}
          </div>
        ))}
      </div>

      {/* Status indicator */}
      <div className={styles.statusRow}>
        <span
          className={[
            styles.statusDot,
            isConnected ? styles.statusDotLive : '',
          ].join(' ')}
        />
        <span className={styles.statusText}>
          {isConnected ? 'Live' : conversation.status === 'connecting' ? 'Connecting…' : 'Ready'}
        </span>
        {isConnected && (
          <span className={[
            styles.speakingIndicator,
            isMuted ? styles.speakingIndicatorMuted : '',
          ].filter(Boolean).join(' ')}>
            {conversation.isSpeaking ? '🔊 Alex' : isMuted ? '🔇 Muted' : '🎙 You'}
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
        <button
          className={[styles.muteFab, isMuted ? styles.muteFabMuted : ''].filter(Boolean).join(' ')}
          onClick={() => setIsMuted(m => !m)}
          aria-label={isMuted ? 'Unmute microphone' : 'Mute microphone'}
        >
          {isMuted ? '🎙 Unmute' : '🔇 Mute'}
        </button>
      </div>

      {/* Error */}
      {connError && (
        <div className={styles.micError}>
          <p className={styles.micErrorText}>Connection failed</p>
          <p className={styles.micErrorSub}>{connError}</p>
        </div>
      )}

      {/* Controls */}
      <div className={styles.controls}>
        {!isConnected ? (
          <Button variant="volt" size="lg" onClick={() => { setConnError(null); start() }}>
            {connError ? 'Try again →' : 'Start interview →'}
          </Button>
        ) : (
          <Button variant="outline" size="md" onClick={stop}>
            End session
          </Button>
        )}
      </div>
    </div>
  )
}

// ── Results ────────────────────────────────────────────────────────────────
function Results({ scores }: { scores: Score[] }) {
  const filled = [...scores]
  while (filled.length < 4) filled.push(0 as Score)

  const avg = scores.length > 0
    ? (scores.reduce((s, v) => s + v, 0) / scores.length).toFixed(1)
    : '—'

  return (
    <div className={styles.phase}>
      <div className={styles.phaseHeader}>
        <div className={styles.stepPill}>Step 3 of 3</div>
        <h1 className={styles.phaseHeadline}>Session complete</h1>
        <p className={styles.phaseSub}>Here's how you scored on the STAR framework.</p>
      </div>

      <div className={styles.resultsGrid}>
        {QUESTIONS.map((q, i) => (
          <div key={i} className={styles.resultRow}>
            <div className={styles.resultLeft}>
              <span className={styles.resultQNum}>Q{i + 1}</span>
              <p className={styles.resultQuestion}>{q}</p>
            </div>
            {scores[i] ? (
              <ScoreIndicator score={scores[i]} />
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
  const [phase, setPhase] = useState<Phase>('quiet-notice')
  const [scores, setScores] = useState<Score[]>([])

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <Link href="/dashboard" className={styles.wordmark}>
          <span className={styles.wordmarkVoid}>interview</span>
          <span className={styles.wordmarkVolt}>AI</span>
        </Link>
        <div className={styles.headerRight}>
          <div className={[
            styles.phasePip,
            phase === 'mic-check' ? styles.phasePipActive : styles.phasePipDone,
          ].join(' ')} />
          <div className={[
            styles.phasePip,
            phase === 'interview' ? styles.phasePipActive : phase === 'results' ? styles.phasePipDone : '',
          ].join(' ')} />
          <div className={[
            styles.phasePip,
            phase === 'results' ? styles.phasePipActive : '',
          ].join(' ')} />
        </div>
      </header>

      <main className={styles.main}>
        {phase === 'quiet-notice' && (
          <QuietNotice onReady={() => setPhase('mic-check')} />
        )}
        {phase === 'mic-check' && (
          <MicCheck onReady={() => setPhase('interview')} />
        )}
        {phase === 'interview' && (
          <Interview
            onComplete={(s) => {
              setScores(s)
              setPhase('results')
            }}
          />
        )}
        {phase === 'results' && (
          <Results scores={scores} />
        )}
      </main>
    </div>
  )
}
