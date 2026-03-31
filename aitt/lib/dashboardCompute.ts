export interface RawSession {
  sessionId: string
  date: string
  score: number
  scores: number[]
  durationMinutes: number
  categories: string[]
  topInsight: string
}

export interface CategoryProgress {
  id: string
  label: string
  currentScore: number
  previousScore: number
  trend: 'up' | 'down' | 'flat'
  sessionCount: number
}

export function computeCategoryProgress(sessions: RawSession[], focusAreas: string[]): CategoryProgress[] {
  return focusAreas.map(label => {
    const id = label.toLowerCase().replace(/\s+/g, '-').replace(/&\s*/g, '')
    const relevant = sessions
      .filter(s => s.categories.includes(label))
      .sort((a, b) => a.date.localeCompare(b.date))

    if (relevant.length === 0) {
      return { id, label, currentScore: 0, previousScore: 0, trend: 'flat' as const, sessionCount: 0 }
    }

    const splitAt = Math.max(relevant.length - 3, 0)
    const recent = relevant.slice(splitAt)
    const prior = relevant.slice(0, splitAt)

    const avg = (arr: RawSession[]) => arr.length === 0 ? 0 : Math.round((arr.reduce((s, r) => s + r.score, 0) / arr.length) * 10) / 10
    const currentScore = avg(recent)
    const previousScore = avg(prior.length > 0 ? prior : recent)
    const diff = currentScore - previousScore
    const trend = diff > 0.05 ? 'up' : diff < -0.05 ? 'down' : 'flat'

    return { id, label, currentScore, previousScore, trend, sessionCount: relevant.length }
  })
}

export function computeStreak(sessions: RawSession[]): number {
  if (sessions.length === 0) return 0

  const dates = new Set(sessions.map(s => s.date))
  let streak = 0
  const today = new Date()

  for (let i = 0; i < 365; i++) {
    const d = new Date(today)
    d.setDate(d.getDate() - i)
    const key = d.toISOString().split('T')[0]
    if (dates.has(key)) {
      streak++
    } else if (i > 0) {
      break
    }
  }

  return streak
}

export function daysUntil(dateStr: string): number {
  const target = new Date(dateStr + 'T12:00:00Z')
  const today = new Date()
  today.setUTCHours(12, 0, 0, 0)
  return Math.round((target.getTime() - today.getTime()) / 86_400_000)
}
