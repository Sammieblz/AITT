import Navbar from '@/components/Navbar/Navbar'
import Footer from '@/components/Footer/Footer'
import Button from '@/components/Button/Button'
import Badge from '@/components/Badge/Badge'
import styles from './page.module.css'

export default function Home() {
  return (
    <>
      <Navbar />
      <main>
        {/* ── Hero ──────────────────────────────────────────────────────── */}
        <section className={styles.hero}>
          <div className={styles.heroInner}>
            <Badge variant="outline" className={styles.heroBadge}>
              Used by 2,400+ job seekers
            </Badge>
            <h1 className={styles.heroHeadline}>
              You&apos;re losing jobs<br />you&apos;re qualified for.
            </h1>
            <p className={styles.heroSub}>
              Most candidates fail behavioral interviews — not because they&apos;re unqualified, but because they&apos;ve never actually practiced. InterviewAI fixes that with real-time AI voice coaching tailored to software engineering roles.
            </p>
            <p className={styles.heroSocial}>
              ★★★★★&nbsp;&nbsp;&quot;Got my L5 offer at Google after 2 weeks of practice.&quot; — Marcus T.
            </p>
            <div className={styles.heroCtas}>
              <Button variant="volt" size="lg" href="/get-started">
                Start practicing free →
              </Button>
              <Button variant="ghost-volt" size="lg" href="/how-it-works">
                See how it works
              </Button>
            </div>
            <div className={styles.trustStrip}>
              <span className={styles.trustItem}>No credit card</span>
              <span className={styles.trustDot}>·</span>
              <span className={styles.trustItem}>Free to start</span>
              <span className={styles.trustDot}>·</span>
              <span className={styles.trustItem}>2,400+ users</span>
              <span className={styles.trustDot}>·</span>
              <span className={styles.trustItem}>ElevenLabs voice AI</span>
            </div>
          </div>
        </section>

        {/* ── Pain ──────────────────────────────────────────────────────── */}
        <section className={styles.pain}>
          <div className={styles.painInner}>
            <p className={styles.painOverline}>Sound familiar?</p>
            <div className={styles.painGrid}>
              <div className={styles.painCard}>
                <div className={styles.painStat}>73%</div>
                <h3 className={styles.painCardTitle}>of candidates fail behavioral rounds</h3>
                <p className={styles.painCardBody}>Not because they&apos;re bad engineers — because they&apos;ve never been coached.</p>
              </div>
              <div className={styles.painCard}>
                <div className={styles.painStat}>4.2x</div>
                <h3 className={styles.painCardTitle}>more likely to get an offer with practice</h3>
                <p className={styles.painCardBody}>Deliberate practice with real feedback is the single biggest differentiator.</p>
              </div>
              <div className={styles.painCard}>
                <div className={styles.painStat}>$40K</div>
                <h3 className={styles.painCardTitle}>average salary difference one level makes</h3>
                <p className={styles.painCardBody}>The interview is the last gate. Don&apos;t let it stop you here.</p>
              </div>
            </div>
          </div>
        </section>

        {/* ── Solution ──────────────────────────────────────────────────── */}
        <section className={styles.solution}>
          <div className={styles.solutionInner}>
            <p className={styles.solutionOverline}>What InterviewAI does</p>
            <h2 className={styles.solutionHeadline}>
              Practice like it&apos;s real.<br />Walk in like you&apos;ve done it before.
            </h2>
            <p className={styles.solutionBody}>
              InterviewAI puts you in a real conversation with an AI interviewer that listens to your voice, scores your answers, and coaches you on exactly what to improve — before the stakes are high.
            </p>

            <div className={styles.featureRows}>
              <div className={styles.featureRow}>
                <div className={styles.featureIcon} style={{ backgroundColor: '#1A3300' }}>
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="9" y="2" width="6" height="12" rx="3" fill="#B4FF5B"/>
                    <path d="M5 10a7 7 0 0 0 14 0" stroke="#B4FF5B" strokeWidth="1.8" strokeLinecap="round"/>
                    <line x1="12" y1="19" x2="12" y2="22" stroke="#B4FF5B" strokeWidth="1.8" strokeLinecap="round"/>
                    <line x1="8" y1="22" x2="16" y2="22" stroke="#B4FF5B" strokeWidth="1.8" strokeLinecap="round"/>
                  </svg>
                </div>
                <div className={styles.featureText}>
                  <h3 className={styles.featureTitle}>Real voice conversation — not typing</h3>
                  <p className={styles.featureDesc}>Speak your answers out loud. The AI listens, responds, and pushes back — just like a real interviewer would.</p>
                </div>
              </div>

              <div className={styles.featureRow}>
                <div className={styles.featureIcon} style={{ backgroundColor: '#1A1A1A' }}>
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <rect x="2" y="2" width="9" height="9" rx="1.5" fill="#FF8800"/>
                    <rect x="13" y="2" width="9" height="9" rx="1.5" fill="#FF8800" opacity="0.5"/>
                    <rect x="2" y="13" width="9" height="9" rx="1.5" fill="#FF8800" opacity="0.5"/>
                    <rect x="13" y="13" width="9" height="9" rx="1.5" fill="#FF8800"/>
                  </svg>
                </div>
                <div className={styles.featureText}>
                  <h3 className={styles.featureTitle}>Instant STAR method feedback</h3>
                  <p className={styles.featureDesc}>Every answer is scored on Situation, Task, Action, and Result. You see exactly where you lost points and how to get them back.</p>
                </div>
              </div>

              <div className={styles.featureRow}>
                <div className={styles.featureIcon} style={{ backgroundColor: '#1A3300' }}>
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="9" stroke="#B4FF5B" strokeWidth="1.8"/>
                    <circle cx="12" cy="12" r="5" stroke="#B4FF5B" strokeWidth="1.8"/>
                    <circle cx="12" cy="12" r="1.5" fill="#B4FF5B"/>
                  </svg>
                </div>
                <div className={styles.featureText}>
                  <h3 className={styles.featureTitle}>Built for software engineering roles</h3>
                  <p className={styles.featureDesc}>Leadership, conflict resolution, technical judgment, failure, impact — we cover every dimension interviewers actually ask about.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── Social Proof Strip ────────────────────────────────────────── */}
        <section className={styles.socialProof}>
          <div className={styles.socialProofInner}>
            <h2 className={styles.socialProofHeadline}>Real people. Real offers.</h2>
            <div className={styles.testimonialGrid}>
              <div className={styles.testimonialCard}>
                <p className={styles.testimonialQuote}>&quot;I bombed 6 interviews in a row. Two weeks with InterviewAI and I had 3 offers. The real-time feedback is unlike anything else out there.&quot;</p>
                <div className={styles.testimonialFooter}>
                  <span className={styles.testimonialName}>Jordan M.</span>
                  <Badge variant="volt">Got offer at Stripe</Badge>
                </div>
              </div>
              <div className={styles.testimonialCard}>
                <p className={styles.testimonialQuote}>&quot;As a career switcher I had no idea how to structure my answers. This tool taught me the STAR method in a way that actually clicked.&quot;</p>
                <div className={styles.testimonialFooter}>
                  <span className={styles.testimonialName}>Priya K.</span>
                  <Badge variant="volt">Hired at Shopify</Badge>
                </div>
              </div>
              <div className={styles.testimonialCard}>
                <p className={styles.testimonialQuote}>&quot;I used to freeze when asked about conflict. Now I have 5 ready stories and the confidence to tell them. This is the cheat code.&quot;</p>
                <div className={styles.testimonialFooter}>
                  <span className={styles.testimonialName}>Devon R.</span>
                  <Badge variant="black">L5 at Amazon</Badge>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── Final CTA ─────────────────────────────────────────────────── */}
        <section className={styles.finalCta}>
          <div className={styles.finalCtaInner}>
            <h2 className={styles.finalCtaHeadline}>
              Your next interview is closer<br />than you think.
            </h2>
            <p className={styles.finalCtaSub}>
              Most engineers are one focused week away from being interview-ready. InterviewAI gets you there faster.
            </p>
            <Button variant="primary" size="lg" href="/get-started">
              Start practicing free →
            </Button>
            <p className={styles.finalCtaNote}>Join 2,400+ engineers who stopped winging it</p>
          </div>
        </section>
      </main>
      <Footer />
    </>
  )
}
