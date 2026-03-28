import Navbar from '@/components/Navbar/Navbar'
import Footer from '@/components/Footer/Footer'
import Button from '@/components/Button/Button'
import Badge from '@/components/Badge/Badge'
import styles from './page.module.css'

export default function HowItWorks() {
  return (
    <>
      <Navbar />
      <main>
        {/* ── Hero ──────────────────────────────────────────────────────── */}
        <section className={styles.hero}>
          <div className={styles.heroInner}>
            <h1 className={styles.heroHeadline}>
              From &quot;I don&apos;t know&quot; to<br />&quot;I&apos;ve got this&quot; — in minutes.
            </h1>
            <p className={styles.heroSub}>
              InterviewAI puts you inside a real interview conversation. You speak, the AI listens, scores your answers, and coaches you on what to improve.
            </p>
          </div>
        </section>

        {/* ── Steps ─────────────────────────────────────────────────────── */}
        <section className={styles.steps}>
          <div className={styles.stepsInner}>
            <div className={styles.step}>
              <div className={styles.stepNumber}>01</div>
              <div className={styles.stepContent}>
                <h2 className={styles.stepTitle}>Tell us your role and level</h2>
                <p className={styles.stepBody}>
                  Pick your job title, target company, and experience level. We use this to personalise the interview — the questions, the expected depth, the scoring bar.
                </p>
                <div className={styles.stepTags}>
                  <Badge variant="black">SWE</Badge>
                  <Badge variant="outline">Entry → Senior</Badge>
                  <Badge variant="volt">2 min setup</Badge>
                </div>
              </div>
            </div>

            <div className={styles.step}>
              <div className={styles.stepNumber}>02</div>
              <div className={styles.stepContent}>
                <h2 className={styles.stepTitle}>The AI starts the interview</h2>
                <p className={styles.stepBody}>
                  You&apos;re dropped straight into the interview. The AI interviewer — powered by ElevenLabs — introduces itself and asks the first question. It sounds real because it is.
                </p>
                <div className={styles.stepTags}>
                  <Badge variant="black">ElevenLabs voice</Badge>
                  <Badge variant="volt">Real time</Badge>
                </div>
              </div>
            </div>

            <div className={styles.step}>
              <div className={styles.stepNumber}>03</div>
              <div className={styles.stepContent}>
                <h2 className={styles.stepTitle}>You answer out loud — naturally</h2>
                <p className={styles.stepBody}>
                  Just talk. The AI listens to everything — structure, confidence, specificity. It follows up when your answer is vague. It pushes back when something doesn&apos;t add up. Exactly like an interviewer would.
                </p>
                <div className={styles.stepTags}>
                  <Badge variant="outline">No typing</Badge>
                  <Badge variant="volt">STAR scoring</Badge>
                </div>
              </div>
            </div>

            <div className={styles.step}>
              <div className={styles.stepNumber}>04</div>
              <div className={styles.stepContent}>
                <h2 className={styles.stepTitle}>Get your score and coaching — immediately</h2>
                <p className={styles.stepBody}>
                  As soon as the session ends you see your full STAR breakdown — Situation, Task, Action, Result — scored 1–5 with specific written coaching on each component. You see exactly what you got wrong and how to fix it.
                </p>
                <div className={styles.stepTags}>
                  <Badge variant="volt">Instant feedback</Badge>
                  <Badge variant="black">Score 1–5</Badge>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* ── CTA ───────────────────────────────────────────────────────── */}
        <section className={styles.cta}>
          <div className={styles.ctaInner}>
            <h2 className={styles.ctaHeadline}>Ready to try it?</h2>
            <p className={styles.ctaSub}>Your first session is free. No card required.</p>
            <Button variant="volt" size="lg" href="/get-started">
              Start your first interview →
            </Button>
          </div>
        </section>
      </main>
      <Footer />
    </>
  )
}
