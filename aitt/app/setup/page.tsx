'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/AuthContext'
import styles from './page.module.css'

const LEVELS = ['Junior', 'Mid-level', 'Senior', 'Staff', 'Principal']
const FOCUS_AREAS = ['Leadership', 'Problem solving', 'Achievement & impact', 'Conflict & collaboration']

export default function SetupPage() {
  const router = useRouter()
  const { user, loading } = useAuth()

  const [targetRole, setTargetRole] = useState('')
  const [targetCompany, setTargetCompany] = useState('')
  const [level, setLevel] = useState('Senior')
  const [focusAreas, setFocusAreas] = useState<string[]>(FOCUS_AREAS)
  const [interviewCompany, setInterviewCompany] = useState('')
  const [interviewRole, setInterviewRole] = useState('')
  const [interviewDate, setInterviewDate] = useState('')
  const [interviewRound, setInterviewRound] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!loading && !user) router.replace('/login')
  }, [loading, user, router])

  function toggleFocus(area: string) {
    setFocusAreas(prev =>
      prev.includes(area) ? prev.filter(a => a !== area) : [...prev, area]
    )
  }

  async function handleSubmit(e: { preventDefault(): void }) {
    e.preventDefault()
    if (!user) return
    setSaving(true)
    setError(null)

    const body: Record<string, unknown> = {
      userId: user.userId,
      name: user.name,
      email: user.email,
      targetRole,
      targetCompany,
      level,
      focusAreas,
      memberSince: new Date().toISOString().split('T')[0],
    }

    if (interviewDate) {
      body.upcomingInterview = {
        company: interviewCompany || targetCompany,
        role: interviewRole || targetRole,
        date: interviewDate,
        round: interviewRound || 'Behavioral interview',
      }
    }

    try {
      const res = await fetch('/api/user', { method: 'PUT', body: JSON.stringify(body), headers: { 'Content-Type': 'application/json' } })
      if (!res.ok) throw new Error('Failed to save profile')
      router.replace('/dashboard')
    } catch {
      setError('Something went wrong. Please try again.')
      setSaving(false)
    }
  }

  if (loading) return null

  return (
    <div className={styles.page}>
      <div className={styles.card}>
        <h1 className={styles.headline}>Set up your profile</h1>
        <p className={styles.sub}>Tell us what you're preparing for.</p>

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.row}>
            <label className={styles.label}>Target role
              <input className={styles.input} value={targetRole} onChange={e => setTargetRole(e.target.value)} placeholder="e.g. Senior Software Engineer" required />
            </label>
            <label className={styles.label}>Target company
              <input className={styles.input} value={targetCompany} onChange={e => setTargetCompany(e.target.value)} placeholder="e.g. Stripe" required />
            </label>
          </div>

          <label className={styles.label}>Level
            <select className={styles.input} value={level} onChange={e => setLevel(e.target.value)}>
              {LEVELS.map(l => <option key={l}>{l}</option>)}
            </select>
          </label>

          <fieldset className={styles.fieldset}>
            <legend className={styles.legend}>Focus areas</legend>
            <div className={styles.checkboxGrid}>
              {FOCUS_AREAS.map(area => (
                <label key={area} className={styles.checkboxLabel}>
                  <input type="checkbox" checked={focusAreas.includes(area)} onChange={() => toggleFocus(area)} />
                  {area}
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset className={styles.fieldset}>
            <legend className={styles.legend}>Upcoming interview <span className={styles.optional}>(optional)</span></legend>
            <div className={styles.row}>
              <label className={styles.label}>Company
                <input className={styles.input} value={interviewCompany} onChange={e => setInterviewCompany(e.target.value)} placeholder={targetCompany || 'Company'} />
              </label>
              <label className={styles.label}>Date
                <input className={styles.input} type="date" value={interviewDate} onChange={e => setInterviewDate(e.target.value)} />
              </label>
            </div>
            <div className={styles.row}>
              <label className={styles.label}>Role
                <input className={styles.input} value={interviewRole} onChange={e => setInterviewRole(e.target.value)} placeholder={targetRole || 'Role'} />
              </label>
              <label className={styles.label}>Round
                <input className={styles.input} value={interviewRound} onChange={e => setInterviewRound(e.target.value)} placeholder="e.g. Final — behavioral panel" />
              </label>
            </div>
          </fieldset>

          {error && <p className={styles.error}>{error}</p>}

          <button type="submit" disabled={saving} className={styles.submit}>
            {saving ? 'Saving…' : 'Go to dashboard →'}
          </button>
        </form>
      </div>
    </div>
  )
}
