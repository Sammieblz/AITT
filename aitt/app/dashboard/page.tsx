'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { CognitoUserPool } from 'amazon-cognito-identity-js'
import Button from '@/components/Button/Button'
import Badge from '@/components/Badge/Badge'
import ScoreIndicator from '@/components/ScoreIndicator/ScoreIndicator'
import ProfileEditModal from './ProfileEditModal'
import { useAuth } from '@/lib/AuthContext'
import { computeCategoryProgress, computeStreak, daysUntil, type RawSession, type CategoryProgress } from '@/lib/dashboardCompute'
import { getTodaysTip } from '@/lib/dailyTips'
import styles from './page.module.css'

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

function formatDate(iso: string): string {
  return new Date(iso + 'T12:00:00Z').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function trendClass(trend: CategoryProgress['trend'], s: Record<string, string>): string {
  if (trend === 'up') return s.trendUp
  if (trend === 'down') return s.trendDown
  return s.trendFlat
}

function trendArrow(trend: CategoryProgress['trend']): string {
  if (trend === 'up') return '↑'
  if (trend === 'down') return '↓'
  return '→'
}

export default function Dashboard() {
  const router = useRouter()
  const { user, loading: authLoading } = useAuth()
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [sessions, setSessions] = useState<RawSession[]>([])
  const [dataLoading, setDataLoading] = useState(true)
  const [editOpen, setEditOpen] = useState(false)

  useEffect(() => {
    if (authLoading) return
    if (!user) { router.replace('/login'); return }

    async function load() {
      const [profileRes, sessionsRes] = await Promise.all([
        fetch(`/api/user?userId=${user!.userId}`),
        fetch(`/api/sessions?userId=${user!.userId}`),
      ])
      if (!profileRes.ok) { router.replace('/setup'); return }
      const profileData = await profileRes.json()
      const sessionsData = sessionsRes.ok ? await sessionsRes.json() : []
      setProfile(profileData)
      setSessions(Array.isArray(sessionsData) ? sessionsData : [])
      setDataLoading(false)
    }

    load()
  }, [authLoading, user, router])

  function handleSignOut() {
    const pool = new CognitoUserPool({
      UserPoolId: process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID!,
      ClientId: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID!,
    })
    pool.getCurrentUser()?.signOut()
    router.replace('/login')
  }

  if (authLoading || dataLoading || !profile) {
    return (
      <div className={styles.page}>
        <div className={styles.loadingState}>Loading…</div>
      </div>
    )
  }

  const recentSessions = sessions.slice(0, 5)
  const avg = sessions.length > 0
    ? (sessions.reduce((s, v) => s + v.score, 0) / sessions.length).toFixed(1)
    : '—'
  const streak = computeStreak(sessions)
  const categoryProgress = computeCategoryProgress(sessions, profile.focusAreas)
  const best = categoryProgress.length > 0
    ? [...categoryProgress].sort((a, b) => b.currentScore - a.currentScore)[0].label
    : '—'
  const tip = getTodaysTip()
  const interview = profile.upcomingInterview
  const interviewDays = interview ? daysUntil(interview.date) : null

  return (
    <div className={styles.page}>
      <header className={styles.appHeader}>
        <div className={styles.appHeaderInner}>
          <Link href="/" className={styles.wordmark} aria-label="AITT home" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <img src="/Logo.png" alt="AITT logo" width={90} height={70} />
            <span style={{ fontWeight: 800 }}>AITT</span>
          </Link>
          <nav className={styles.appNav}>
            <span className={styles.appNavItem}>Dashboard</span>
          </nav>
          <div className={styles.appHeaderRight}>
            <Badge variant="volt">{streak}-day streak</Badge>
            <Button variant="volt" size="sm" href="/session">New session →</Button>
            <Button variant="outline" size="sm" onClick={handleSignOut}>Sign out</Button>
          </div>
        </div>
      </header>

      <main className={styles.main}>
        {/* Welcome */}
        <section className={styles.welcome}>
          <div>
            <p className={styles.welcomeGreeting}>Good {greeting()}, {profile.name.split(' ')[0]}</p>
            <h1 className={styles.welcomeHeadline}>
              Prep for{' '}
              <span className={styles.welcomeHeadlineAccent}>{profile.targetCompany}</span>
            </h1>
            <p className={styles.welcomeSub}>{profile.targetRole} · {profile.level}</p>
          </div>
          <div className={styles.welcomeBadges}>
            <Badge variant="black">{streak} day streak 🔥</Badge>
            {interviewDays !== null && (
              <Badge variant="outline">{interviewDays} days until interview</Badge>
            )}
            <button className={styles.editProfileBtn} onClick={() => setEditOpen(true)}>
              Edit profile
            </button>
          </div>
        </section>

        {/* Stats strip */}
        <div className={styles.statsStrip}>
          <div className={styles.statCard}>
            <span className={styles.statValue}>{sessions.length}</span>
            <span className={styles.statLabel}>Total sessions</span>
            <span className={styles.statSub}>all time</span>
          </div>
          <div className={styles.statCard}>
            <span className={styles.statValue}>{avg}</span>
            <span className={styles.statLabel}>Avg STAR score</span>
            <span className={styles.statSub}>out of 5.0</span>
          </div>
          <div className={styles.statCard}>
            <span className={styles.statValue}>{best}</span>
            <span className={styles.statLabel}>Best category</span>
            <span className={styles.statSub}>keep sharpening it</span>
          </div>
          <div className={styles.statCard}>
            <span className={styles.statValue}>{interviewDays !== null ? `${interviewDays}d` : '—'}</span>
            <span className={styles.statLabel}>Until interview</span>
            <span className={styles.statSub}>
              {interview ? `${formatDate(interview.date)} · ${interview.company}` : 'Not set'}
            </span>
          </div>
        </div>

        {/* Action row */}
        <div className={styles.actionRow}>
          <div className={styles.startPracticeCard}>
            <div>
              <p className={styles.actionOverline}>Ready to practice?</p>
              <h2 className={styles.actionHeadline}>Start a session</h2>
              <p className={styles.actionSub}>
                {sessions.length === 0
                  ? 'Start your first session to begin tracking your progress.'
                  : `You've completed ${sessions.length} session${sessions.length !== 1 ? 's' : ''}. Keep the momentum going.`}
              </p>
            </div>
            <div className={styles.actionFocusList}>
              {profile.focusAreas.map(area => <Badge key={area} variant="outline">{area}</Badge>)}
            </div>
            <Button variant="volt" size="lg" href="/session">Start practice session →</Button>
          </div>

          {interview ? (
            <div className={styles.upcomingCard}>
              <Badge variant="alert">{interviewDays} days</Badge>
              <p className={styles.upcomingLabel}>Upcoming interview</p>
              <p className={styles.upcomingCompany}>{interview.company}</p>
              <p className={styles.upcomingRole}>{interview.role}</p>
              <p className={styles.upcomingRound}>{interview.round}</p>
              <p className={styles.upcomingDate}>{formatDate(interview.date)}</p>
            </div>
          ) : (
            <div className={styles.upcomingCard}>
              <p className={styles.upcomingLabel}>No interview scheduled</p>
              <button className={styles.editProfileBtn} onClick={() => setEditOpen(true)}>
                Add interview date →
              </button>
            </div>
          )}
        </div>

        {/* Recent sessions */}
        <section>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>Recent sessions</h2>
            <span className={styles.sectionMeta}>{sessions.length} total</span>
          </div>
          {recentSessions.length === 0 ? (
            <p style={{ color: '#666', padding: '1rem 0' }}>No sessions yet — start your first one above.</p>
          ) : (
            <ul className={styles.sessionsList}>
              {recentSessions.map(session => (
                <li key={session.sessionId} className={styles.sessionRow}>
                  <ScoreIndicator score={Math.round(session.score) as 1|2|3|4|5} />
                  <div className={styles.sessionMeta}>
                    <span className={styles.sessionDate}>{formatDate(session.date)}</span>
                    <span className={styles.sessionDuration}>{session.durationMinutes} min</span>
                  </div>
                  <p className={styles.sessionInsight}>{session.topInsight}</p>
                  <div className={styles.sessionCategories}>
                    {session.categories.map(cat => <Badge key={cat} variant="white">{cat}</Badge>)}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        {/* Bottom row */}
        <div className={styles.bottomRow}>
          <div className={styles.progressCard}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>Category progress</h2>
              <span className={styles.sectionMeta}>score out of 5.0</span>
            </div>
            <div className={styles.categoryRows}>
              {categoryProgress.map(cat => (
                <div key={cat.id} className={styles.categoryRow}>
                  <div className={styles.categoryMeta}>
                    <span className={styles.categoryName}>{cat.label}</span>
                    <div className={styles.categoryRight}>
                      <span className={trendClass(cat.trend, styles)}>
                        {trendArrow(cat.trend)} {Math.abs(cat.currentScore - cat.previousScore).toFixed(1)}
                      </span>
                      <span className={styles.categoryScore}>{cat.currentScore}</span>
                    </div>
                  </div>
                  <div className={styles.barTrack}>
                    <div className={styles.barFill} style={{ width: `${(cat.currentScore / 5) * 100}%` }} />
                  </div>
                  <span className={styles.categorySessionCount}>
                    {cat.sessionCount} session{cat.sessionCount !== 1 ? 's' : ''}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className={styles.tipCard}>
            <div className={styles.tipHeader}>
              <Badge variant="volt">{tip.category}</Badge>
              <span className={styles.tipDate}>{formatDate(new Date().toISOString().split('T')[0])}</span>
            </div>
            <h3 className={styles.tipHeadline}>{tip.headline}</h3>
            <p className={styles.tipBody}>{tip.body}</p>
          </div>
        </div>
      </main>

      {editOpen && (
        <ProfileEditModal
          profile={profile}
          onClose={() => setEditOpen(false)}
          onSave={updated => { setProfile(updated); setEditOpen(false) }}
        />
      )}
    </div>
  )
}

function greeting() {
  const h = new Date().getHours()
  if (h < 12) return 'morning'
  if (h < 17) return 'afternoon'
  return 'evening'
}
