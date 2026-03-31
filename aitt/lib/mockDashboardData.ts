// ── Types ──────────────────────────────────────────────────────────────────

export interface UserProfile {
  name: string
  targetRole: string
  targetCompany: string
  level: string
  focusAreas: string[]
  practiceStreakDays: number
  memberSince: string
}

export interface UpcomingInterview {
  company: string
  role: string
  date: string
  daysUntil: number
  round: string
}

// score must be the literal union to satisfy ScoreIndicator's type constraint
export interface Session {
  id: string
  date: string
  durationMinutes: number
  categories: string[]
  score: 1 | 2 | 3 | 4 | 5
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

export interface DailyTip {
  date: string
  headline: string
  body: string
  category: string
}

// ── Mock data ──────────────────────────────────────────────────────────────

export const mockUser: UserProfile = {
  name: 'Alex',
  targetRole: 'Senior Software Engineer',
  targetCompany: 'Stripe',
  level: 'Senior',
  focusAreas: ['Leadership', 'Problem solving', 'Achievement & impact', 'Conflict & collaboration'],
  practiceStreakDays: 4,
  memberSince: '2026-03-14',
}

export const mockUpcomingInterview: UpcomingInterview = {
  company: 'Stripe',
  role: 'Senior Software Engineer',
  date: '2026-04-02',
  daysUntil: 5,
  round: 'Final — behavioral panel',
}

// Most recent first. Scores arc: 3 → 3 → 3 → 4 → 4 → 4 → 4
export const mockSessions: Session[] = [
  {
    id: 's7',
    date: '2026-03-27',
    durationMinutes: 28,
    categories: ['Leadership', 'Conflict & collaboration'],
    score: 4,
    topInsight: 'Strong Result framing — quantify the team impact more explicitly.',
  },
  {
    id: 's6',
    date: '2026-03-26',
    durationMinutes: 22,
    categories: ['Achievement & impact'],
    score: 4,
    topInsight: 'Great STAR structure; slow your delivery on the Action section.',
  },
  {
    id: 's5',
    date: '2026-03-25',
    durationMinutes: 31,
    categories: ['Problem solving', 'Conflict & collaboration'],
    score: 4,
    topInsight: 'Situation context was clear and concise — keep that length.',
  },
  {
    id: 's4',
    date: '2026-03-22',
    durationMinutes: 19,
    categories: ['Leadership'],
    score: 4,
    topInsight: 'Excellent use of "I" vs "we" — ownership came through strongly.',
  },
  {
    id: 's3',
    date: '2026-03-19',
    durationMinutes: 24,
    categories: ['Achievement & impact', 'Leadership'],
    score: 3,
    topInsight: 'Result section was vague — add a metric or timeline to anchor it.',
  },
  {
    id: 's2',
    date: '2026-03-17',
    durationMinutes: 20,
    categories: ['Conflict & collaboration'],
    score: 3,
    topInsight: 'Too much setup before the Task — cut the Situation by one-third.',
  },
  {
    id: 's1',
    date: '2026-03-14',
    durationMinutes: 18,
    categories: ['Problem solving'],
    score: 3,
    topInsight: 'Good instincts — answer lacked a concrete Result; add a number.',
  },
]

export const mockCategoryProgress: CategoryProgress[] = [
  {
    id: 'leadership',
    label: 'Leadership',
    currentScore: 4.0,
    previousScore: 3.3,
    trend: 'up',
    sessionCount: 3,
  },
  {
    id: 'problem-solving',
    label: 'Problem solving',
    currentScore: 3.8,
    previousScore: 3.0,
    trend: 'up',
    sessionCount: 2,
  },
  {
    id: 'achievement',
    label: 'Achievement & impact',
    currentScore: 3.5,
    previousScore: 3.5,
    trend: 'flat',
    sessionCount: 2,
  },
  {
    id: 'conflict',
    label: 'Conflict & collaboration',
    currentScore: 3.7,
    previousScore: 3.2,
    trend: 'up',
    sessionCount: 2,
  },
]

export const mockDailyTip: DailyTip = {
  date: '2026-03-28',
  headline: 'Open with the outcome.',
  body: 'Interviewers lose interest if the story payoff is buried. Lead your Result in the first sentence — "We shipped on time and reduced churn by 18%" — then walk back through how you got there. It signals confidence and keeps them engaged throughout.',
  category: 'STAR method',
}
