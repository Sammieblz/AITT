'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import Button from '@/components/Button/Button'
import styles from './page.module.css'

const LEVELS = ['Entry level', 'Mid-level', 'Senior']

const CATEGORIES = [
  { id: 'leadership', label: 'Leadership', desc: 'Show how you guide teams and decisions' },
  { id: 'conflict', label: 'Conflict & collaboration', desc: 'Navigate disagreement and work with others' },
  { id: 'problem', label: 'Problem solving', desc: 'Break down ambiguous challenges' },
  { id: 'failure', label: 'Failure & resilience', desc: 'Own mistakes and grow from setbacks' },
  { id: 'achievement', label: 'Achievement & impact', desc: 'Quantify your wins and contributions' },
  { id: 'adaptability', label: 'Adaptability', desc: 'Thrive through change and uncertainty' },
]

export default function GetStarted() {
  const router = useRouter()
  const [step, setStep] = useState(0)
  const [level, setLevel] = useState<string | null>(null)
  const [categories, setCategories] = useState<string[]>([])
  const [micReady, setMicReady] = useState(false)

  const toggleCategory = (id: string) => {
    setCategories((prev) =>
      prev.includes(id) ? prev.filter((c) => c !== id) : [...prev, id]
    )
  }

  const stepLabels = ['Your role', 'Your focus', 'Mic check']

  return (
    <div className={styles.page}>
      {/* Wordmark */}
      <div className={styles.wordmarkWrap}>
        <Link href="/" className={styles.wordmark}>
          <span className={styles.wordmarkVoid}>interview</span>
          <span className={styles.wordmarkVolt}>AI</span>
        </Link>
      </div>

      {/* Card */}
      <div className={styles.card}>
        {/* Step Indicator */}
        <div className={styles.stepIndicator}>
          {stepLabels.map((label, i) => (
            <div key={label} className={styles.stepIndicatorItem}>
              <div
                className={[
                  styles.stepDot,
                  i < step ? styles.stepDotCompleted : '',
                  i === step ? styles.stepDotCurrent : '',
                  i > step ? styles.stepDotUpcoming : '',
                ].filter(Boolean).join(' ')}
              />
              <span className={styles.stepDotLabel}>{label}</span>
            </div>
          ))}
        </div>

        {/* Step 1 */}
        {step === 0 && (
          <div className={styles.stepContent}>
            <h1 className={styles.stepHeadline}>What role are you going for?</h1>
            <p className={styles.stepSub}>Tell us about the position so we can personalize your interview.</p>

            <input
              type="text"
              placeholder="e.g. Software Engineer, Data Scientist"
              className={styles.input}
            />
            <input
              type="text"
              placeholder="e.g. Google, Stripe, startup (optional)"
              className={styles.input}
            />

            <div className={styles.levelSelector}>
              {LEVELS.map((l) => (
                <button
                  key={l}
                  type="button"
                  className={[
                    styles.levelBtn,
                    level === l ? styles.levelBtnSelected : '',
                  ].filter(Boolean).join(' ')}
                  onClick={() => setLevel(l)}
                >
                  {l}
                </button>
              ))}
            </div>

            <Button variant="volt" size="md" fullWidth onClick={() => setStep(1)}>
              Continue →
            </Button>
            <p className={styles.stepNote}>Takes 90 seconds. No card required.</p>
          </div>
        )}

        {/* Step 2 */}
        {step === 1 && (
          <div className={styles.stepContent}>
            <h1 className={styles.stepHeadline}>What do you want to work on?</h1>
            <p className={styles.stepSub}>Pick the areas you want to focus on. You can always change this later.</p>

            <div className={styles.categoryGrid}>
              {CATEGORIES.map((cat) => (
                <button
                  key={cat.id}
                  type="button"
                  className={[
                    styles.categoryCard,
                    categories.includes(cat.id) ? styles.categoryCardSelected : '',
                  ].filter(Boolean).join(' ')}
                  onClick={() => toggleCategory(cat.id)}
                >
                  <span className={styles.categoryLabel}>{cat.label}</span>
                  <span className={styles.categoryDesc}>{cat.desc}</span>
                </button>
              ))}
            </div>

            <Button variant="volt" size="md" fullWidth onClick={() => setStep(2)}>
              Continue →
            </Button>
            <button type="button" className={styles.backBtn} onClick={() => setStep(0)}>
              ← Back
            </button>
          </div>
        )}

        {/* Step 3 */}
        {step === 2 && (
          <div className={styles.stepContent}>
            <h1 className={styles.stepHeadline}>Check your mic.</h1>
            <p className={styles.stepSub}>Make sure we can hear you before we start.</p>

            <div className={styles.micWrap}>
              <button
                type="button"
                className={[styles.micBtn, micReady ? styles.micBtnReady : ''].filter(Boolean).join(' ')}
                onClick={() => setMicReady((v) => !v)}
                aria-label="Test microphone"
              >
                <svg
                  width="28"
                  height="28"
                  viewBox="0 0 24 24"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <rect
                    x="9"
                    y="2"
                    width="6"
                    height="12"
                    rx="3"
                    fill={micReady ? '#0A0A0A' : '#B4FF5B'}
                  />
                  <path
                    d="M5 10a7 7 0 0 0 14 0"
                    stroke={micReady ? '#0A0A0A' : '#B4FF5B'}
                    strokeWidth="1.8"
                    strokeLinecap="round"
                  />
                  <line
                    x1="12"
                    y1="19"
                    x2="12"
                    y2="22"
                    stroke={micReady ? '#0A0A0A' : '#B4FF5B'}
                    strokeWidth="1.8"
                    strokeLinecap="round"
                  />
                  <line
                    x1="8"
                    y1="22"
                    x2="16"
                    y2="22"
                    stroke={micReady ? '#0A0A0A' : '#B4FF5B'}
                    strokeWidth="1.8"
                    strokeLinecap="round"
                  />
                </svg>
              </button>
              <p className={styles.micLabel}>
                {micReady ? (
                  <span className={styles.micReady}>Microphone ready ✓</span>
                ) : (
                  'Click to test microphone'
                )}
              </p>
            </div>

            <Button
              variant="volt"
              size="md"
              fullWidth
              disabled={!micReady}
              onClick={() => router.push('/dashboard')}
            >
              Start my first interview →
            </Button>
            <p className={styles.micNote}>Your audio is never stored. Sessions are private.</p>
            <button type="button" className={styles.backBtn} onClick={() => setStep(1)}>
              ← Back
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
