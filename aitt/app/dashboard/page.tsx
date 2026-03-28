import Link from 'next/link'
import Button from '@/components/Button/Button'
import Badge from '@/components/Badge/Badge'
import ScoreIndicator from '@/components/ScoreIndicator/ScoreIndicator'
import {
  mockUser,
  mockUpcomingInterview,
  mockSessions,
  mockCategoryProgress,
  mockDailyTip,
  type CategoryProgress,
} from '@/lib/mockDashboardData'
import styles from './page.module.css'

function formatDate(iso: string): string {
  // Use noon UTC to avoid off-by-one from timezone offsets on the server
  return new Date(iso + 'T12:00:00Z').toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
  })
}

function avgScore(sessions: typeof mockSessions): string {
  const sum = sessions.reduce((acc, s) => acc + s.score, 0)
  return (sum / sessions.length).toFixed(1)
}

function trendClass(trend: CategoryProgress['trend']): string {
  if (trend === 'up') return styles.trendUp
  if (trend === 'down') return styles.trendDown
  return styles.trendFlat
}

function trendArrow(trend: CategoryProgress['trend']): string {
  if (trend === 'up') return '↑'
  if (trend === 'down') return '↓'
  return '→'
}

function bestCategory(cats: typeof mockCategoryProgress): string {
  return [...cats].sort((a, b) => b.currentScore - a.currentScore)[0].label
}

export default function Dashboard() {
  const recentSessions = mockSessions.slice(0, 5)
  const avg = avgScore(mockSessions)
  const best = bestCategory(mockCategoryProgress)

  return (
    <div className={styles.page}>
      {/* ── App Header ──────────────────────────────────────────────────── */}
      <header className={styles.appHeader}>
        <div className={styles.appHeaderInner}>
          <Link href="/" className={styles.wordmark}>
            <span className={styles.wordmarkVoid}>interview</span>
            <span className={styles.wordmarkVolt}>AI</span>
          </Link>
          <nav className={styles.appNav}>
            <span className={styles.appNavItem}>Dashboard</span>
          </nav>
          <div className={styles.appHeaderRight}>
            <Badge variant="volt">{mockUser.practiceStreakDays}-day streak</Badge>
            <Button variant="volt" size="sm" href="/session">New session →</Button>
          </div>
        </div>
      </header>

      <main className={styles.main}>
        {/* ── Welcome ───────────────────────────────────────────────────── */}
        <section className={styles.welcome}>
          <div>
            <p className={styles.welcomeGreeting}>Good morning, {mockUser.name}</p>
            <h1 className={styles.welcomeHeadline}>
              Prep for{' '}
              <span className={styles.welcomeHeadlineAccent}>{mockUser.targetCompany}</span>
            </h1>
            <p className={styles.welcomeSub}>
              {mockUser.targetRole} · {mockUser.level}
            </p>
          </div>
          <div className={styles.welcomeBadges}>
            <Badge variant="black">{mockUser.practiceStreakDays} day streak 🔥</Badge>
            <Badge variant="outline">{mockUpcomingInterview.daysUntil} days until interview</Badge>
          </div>
        </section>

        {/* ── Stats strip ───────────────────────────────────────────────── */}
        <div className={styles.statsStrip}>
          <div className={styles.statCard}>
            <span className={styles.statValue}>{mockSessions.length}</span>
            <span className={styles.statLabel}>Total sessions</span>
            <span className={styles.statSub}>past 2 weeks</span>
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
            <span className={styles.statValue}>{mockUpcomingInterview.daysUntil}d</span>
            <span className={styles.statLabel}>Until interview</span>
            <span className={styles.statSub}>
              {formatDate(mockUpcomingInterview.date)} · {mockUpcomingInterview.company}
            </span>
          </div>
        </div>

        {/* ── Action row ────────────────────────────────────────────────── */}
        <div className={styles.actionRow}>
          {/* Start practice card */}
          <div className={styles.startPracticeCard}>
            <div>
              <p className={styles.actionOverline}>Ready to practice?</p>
              <h2 className={styles.actionHeadline}>Start a session</h2>
              <p className={styles.actionSub}>
                Your recent sessions show growth in Leadership and Problem solving.
                Push on Achievement & impact — it&apos;s your lowest recent score.
              </p>
            </div>
            <div className={styles.actionFocusList}>
              {mockUser.focusAreas.map((area) => (
                <Badge key={area} variant="outline">{area}</Badge>
              ))}
            </div>
            <Button variant="volt" size="lg" href="/session">
              Start practice session →
            </Button>
          </div>

          {/* Upcoming interview card */}
          <div className={styles.upcomingCard}>
            <Badge variant="alert">{mockUpcomingInterview.daysUntil} days</Badge>
            <p className={styles.upcomingLabel}>Upcoming interview</p>
            <p className={styles.upcomingCompany}>{mockUpcomingInterview.company}</p>
            <p className={styles.upcomingRole}>{mockUpcomingInterview.role}</p>
            <p className={styles.upcomingRound}>{mockUpcomingInterview.round}</p>
            <p className={styles.upcomingDate}>
              {formatDate(mockUpcomingInterview.date)}, 2026
            </p>
          </div>
        </div>

        {/* ── Recent sessions ───────────────────────────────────────────── */}
        <section>
          <div className={styles.sectionHeader}>
            <h2 className={styles.sectionTitle}>Recent sessions</h2>
            <span className={styles.sectionMeta}>{mockSessions.length} total</span>
          </div>
          <ul className={styles.sessionsList}>
            {recentSessions.map((session) => (
              <li key={session.id} className={styles.sessionRow}>
                <ScoreIndicator score={session.score} />
                <div className={styles.sessionMeta}>
                  <span className={styles.sessionDate}>{formatDate(session.date)}</span>
                  <span className={styles.sessionDuration}>{session.durationMinutes} min</span>
                </div>
                <p className={styles.sessionInsight}>{session.topInsight}</p>
                <div className={styles.sessionCategories}>
                  {session.categories.map((cat) => (
                    <Badge key={cat} variant="white">{cat}</Badge>
                  ))}
                </div>
              </li>
            ))}
          </ul>
        </section>

        {/* ── Bottom row: progress + tip ─────────────────────────────────── */}
        <div className={styles.bottomRow}>
          {/* Category progress */}
          <div className={styles.progressCard}>
            <div className={styles.sectionHeader}>
              <h2 className={styles.sectionTitle}>Category progress</h2>
              <span className={styles.sectionMeta}>score out of 5.0</span>
            </div>
            <div className={styles.categoryRows}>
              {mockCategoryProgress.map((cat) => (
                <div key={cat.id} className={styles.categoryRow}>
                  <div className={styles.categoryMeta}>
                    <span className={styles.categoryName}>{cat.label}</span>
                    <div className={styles.categoryRight}>
                      <span className={trendClass(cat.trend)}>
                        {trendArrow(cat.trend)} {Math.abs(cat.currentScore - cat.previousScore).toFixed(1)}
                      </span>
                      <span className={styles.categoryScore}>{cat.currentScore}</span>
                    </div>
                  </div>
                  <div className={styles.barTrack}>
                    <div
                      className={styles.barFill}
                      style={{ width: `${(cat.currentScore / 5) * 100}%` }}
                    />
                  </div>
                  <span className={styles.categorySessionCount}>
                    {cat.sessionCount} session{cat.sessionCount !== 1 ? 's' : ''}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Daily tip */}
          <div className={styles.tipCard}>
            <div className={styles.tipHeader}>
              <Badge variant="volt">{mockDailyTip.category}</Badge>
              <span className={styles.tipDate}>{formatDate(mockDailyTip.date)}</span>
            </div>
            <h3 className={styles.tipHeadline}>{mockDailyTip.headline}</h3>
            <p className={styles.tipBody}>{mockDailyTip.body}</p>
          </div>
        </div>
      </main>
    </div>
  )
}
