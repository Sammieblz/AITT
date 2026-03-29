'use client'

import { useState } from 'react'
import { useAuth } from '@/lib/AuthContext'

interface UserProfile {
  userId: string
  name: string
  targetRole: string
  targetCompany: string
  level: string
  focusAreas: string[]
  memberSince: string
  upcomingInterview?: { company: string; role: string; date: string; round: string }
}

const LEVELS = ['Junior', 'Mid-level', 'Senior', 'Staff', 'Principal']
const FOCUS_AREAS = ['Leadership', 'Problem solving', 'Achievement & impact', 'Conflict & collaboration']

interface Props {
  profile: UserProfile
  onClose: () => void
  onSave: (updated: UserProfile) => void
}

export default function ProfileEditModal({ profile, onClose, onSave }: Props) {
  const { user } = useAuth()
  const [targetRole, setTargetRole] = useState(profile.targetRole)
  const [targetCompany, setTargetCompany] = useState(profile.targetCompany)
  const [level, setLevel] = useState(profile.level)
  const [focusAreas, setFocusAreas] = useState<string[]>(profile.focusAreas)
  const [interviewCompany, setInterviewCompany] = useState(profile.upcomingInterview?.company ?? '')
  const [interviewRole, setInterviewRole] = useState(profile.upcomingInterview?.role ?? '')
  const [interviewDate, setInterviewDate] = useState(profile.upcomingInterview?.date ?? '')
  const [interviewRound, setInterviewRound] = useState(profile.upcomingInterview?.round ?? '')
  const [saving, setSaving] = useState(false)

  function toggleFocus(area: string) {
    setFocusAreas(prev => prev.includes(area) ? prev.filter(a => a !== area) : [...prev, area])
  }

  async function handleSubmit(e: { preventDefault(): void }) {
    e.preventDefault()
    if (!user) return
    setSaving(true)

    const updated: UserProfile = {
      ...profile,
      targetRole,
      targetCompany,
      level,
      focusAreas,
      upcomingInterview: interviewDate ? {
        company: interviewCompany || targetCompany,
        role: interviewRole || targetRole,
        date: interviewDate,
        round: interviewRound || 'Behavioral interview',
      } : undefined,
    }

    await fetch('/api/user', { method: 'PUT', body: JSON.stringify(updated), headers: { 'Content-Type': 'application/json' } })
    onSave(updated)
  }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 100, padding: '1rem' }}>
      <div style={{ background: '#111', border: '1px solid #222', borderRadius: 16, padding: '2rem', width: '100%', maxWidth: 520, maxHeight: '90vh', overflowY: 'auto' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ fontFamily: 'var(--font-syne)', fontWeight: 800, fontSize: '1.25rem', color: '#fff' }}>Edit profile</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#888', cursor: 'pointer', fontSize: '1.25rem' }}>✕</button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <label style={labelStyle}>Target role
            <input style={inputStyle} value={targetRole} onChange={e => setTargetRole(e.target.value)} required />
          </label>
          <label style={labelStyle}>Target company
            <input style={inputStyle} value={targetCompany} onChange={e => setTargetCompany(e.target.value)} required />
          </label>
          <label style={labelStyle}>Level
            <select style={inputStyle} value={level} onChange={e => setLevel(e.target.value)}>
              {LEVELS.map(l => <option key={l}>{l}</option>)}
            </select>
          </label>

          <fieldset style={{ border: '1px solid #222', borderRadius: 8, padding: '0.75rem 1rem' }}>
            <legend style={{ color: '#aaa', fontSize: '0.85rem', padding: '0 0.25rem' }}>Focus areas</legend>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginTop: '0.5rem' }}>
              {FOCUS_AREAS.map(area => (
                <label key={area} style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.875rem', color: '#ccc', cursor: 'pointer' }}>
                  <input type="checkbox" checked={focusAreas.includes(area)} onChange={() => toggleFocus(area)} />
                  {area}
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset style={{ border: '1px solid #222', borderRadius: 8, padding: '0.75rem 1rem' }}>
            <legend style={{ color: '#aaa', fontSize: '0.85rem', padding: '0 0.25rem' }}>Upcoming interview <span style={{ color: '#555' }}>(optional)</span></legend>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem', marginTop: '0.5rem' }}>
              <label style={labelStyle}>Company <input style={inputStyle} value={interviewCompany} onChange={e => setInterviewCompany(e.target.value)} /></label>
              <label style={labelStyle}>Date <input style={inputStyle} type="date" value={interviewDate} onChange={e => setInterviewDate(e.target.value)} /></label>
              <label style={labelStyle}>Role <input style={inputStyle} value={interviewRole} onChange={e => setInterviewRole(e.target.value)} /></label>
              <label style={labelStyle}>Round <input style={inputStyle} value={interviewRound} onChange={e => setInterviewRound(e.target.value)} /></label>
            </div>
          </fieldset>

          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
            <button type="button" onClick={onClose} style={{ padding: '0.65rem 1.25rem', borderRadius: 8, border: '1px solid #333', background: 'none', color: '#aaa', cursor: 'pointer' }}>
              Cancel
            </button>
            <button type="submit" disabled={saving} style={{ padding: '0.65rem 1.25rem', borderRadius: 8, background: '#B4FF5B', color: '#000', fontWeight: 700, border: 'none', cursor: saving ? 'not-allowed' : 'pointer', opacity: saving ? 0.7 : 1 }}>
              {saving ? 'Saving…' : 'Save changes'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

const labelStyle: React.CSSProperties = { display: 'flex', flexDirection: 'column', gap: '0.35rem', fontSize: '0.8rem', color: '#aaa' }
const inputStyle: React.CSSProperties = { padding: '0.6rem 0.75rem', background: '#1a1a1a', border: '1px solid #333', borderRadius: 8, color: '#fff', fontSize: '0.9rem', outline: 'none' }
