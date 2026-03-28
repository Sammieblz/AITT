import Navbar from '@/components/Navbar/Navbar'
import Footer from '@/components/Footer/Footer'
import Button from '@/components/Button/Button'
import Badge from '@/components/Badge/Badge'
import styles from './page.module.css'

export default function Pricing() {
  return (
    <>
      <Navbar />
      <main>
        {/* ── Hero ──────────────────────────────────────────────────────── */}
        <section className={styles.hero}>
          <div className={styles.heroInner}>
            <h1 className={styles.heroHeadline}>
              Simple pricing.<br />No gotchas.
            </h1>
            <p className={styles.heroSub}>
              Start free. Upgrade when you&apos;re ready.<br />Cancel anytime.
            </p>
          </div>
        </section>

        {/* ── Pricing Cards ─────────────────────────────────────────────── */}
        <section className={styles.cards}>
          <div className={styles.cardsInner}>
            {/* Free */}
            <div className={styles.cardFree}>
              <Badge variant="outline" className={styles.cardBadge}>Free forever</Badge>
              <h2 className={styles.cardName}>Starter</h2>
              <div className={styles.cardPriceRow}>
                <span className={styles.cardPrice}>$0</span>
                <span className={styles.cardPricePer}>/month</span>
              </div>
              <hr className={styles.cardDivider} />
              <ul className={styles.featureList}>
                <li className={styles.featureItem}>
                  <span className={styles.featureCheck}>✓</span>
                  <span>3 mock interviews/month</span>
                </li>
                <li className={styles.featureItem}>
                  <span className={styles.featureCheck}>✓</span>
                  <span>All 6 question categories</span>
                </li>
                <li className={styles.featureItem}>
                  <span className={styles.featureCheck}>✓</span>
                  <span>STAR scoring</span>
                </li>
                <li className={styles.featureItem}>
                  <span className={styles.featureCheck}>✓</span>
                  <span>Session summary</span>
                </li>
                <li className={styles.featureItem}>
                  <span className={styles.featureCheck}>✓</span>
                  <span>Text feedback</span>
                </li>
              </ul>
              <Button variant="outline" size="md" fullWidth href="/get-started">
                Get started free
              </Button>
            </div>

            {/* Pro */}
            <div className={styles.cardPro}>
              <Badge variant="volt" className={styles.cardBadge}>Most popular</Badge>
              <h2 className={styles.cardNamePro}>Pro</h2>
              <div className={styles.cardPriceRow}>
                <span className={styles.cardPricePro}>$19</span>
                <span className={styles.cardPricePerPro}>/month</span>
              </div>
              <p className={styles.cardAnnual}>or $149/year — save 35%</p>
              <hr className={styles.cardDividerDark} />
              <ul className={styles.featureList}>
                <li className={styles.featureItemPro}>
                  <span className={styles.featureCheckVolt}>✓</span>
                  <span>Unlimited mock interviews</span>
                </li>
                <li className={styles.featureItemPro}>
                  <span className={styles.featureCheckVolt}>✓</span>
                  <span>Real-time voice conversation (ElevenLabs)</span>
                </li>
                <li className={styles.featureItemPro}>
                  <span className={styles.featureCheckVolt}>✓</span>
                  <span>Full STAR scoring + coaching</span>
                </li>
                <li className={styles.featureItemPro}>
                  <span className={styles.featureCheckVolt}>✓</span>
                  <span>Role and level personalization</span>
                </li>
                <li className={styles.featureItemPro}>
                  <span className={styles.featureCheckVolt}>✓</span>
                  <span>Progress tracking</span>
                </li>
                <li className={styles.featureItemPro}>
                  <span className={styles.featureCheckVolt}>✓</span>
                  <span>Senior-level question bank</span>
                </li>
                <li className={styles.featureItemPro}>
                  <span className={styles.featureCheckVolt}>✓</span>
                  <span>Priority access to new features</span>
                </li>
              </ul>
              <Button variant="volt" size="md" fullWidth href="/get-started">
                Start 7-day free trial →
              </Button>
              <p className={styles.cardNoCard}>No credit card to start</p>
            </div>
          </div>
        </section>

        {/* ── FAQ ───────────────────────────────────────────────────────── */}
        <section className={styles.faq}>
          <div className={styles.faqInner}>
            <h2 className={styles.faqHeadline}>Questions.</h2>

            <div className={styles.faqItem}>
              <h3 className={styles.faqQuestion}>Is the free plan actually free — no card, no trial?</h3>
              <p className={styles.faqAnswer}>Yes. Three full mock interviews per month, no credit card, no time limit. We want you to try it before you commit.</p>
            </div>

            <div className={styles.faqItem}>
              <h3 className={styles.faqQuestion}>How is this different from practicing with a friend or ChatGPT?</h3>
              <p className={styles.faqAnswer}>A friend doesn&apos;t know the STAR method and won&apos;t push back consistently. ChatGPT can&apos;t hear you. InterviewAI listens to your actual voice, evaluates your structure in real time, and gives you specific coaching — not generic feedback.</p>
            </div>

            <div className={styles.faqItem}>
              <h3 className={styles.faqQuestion}>What roles and levels does it support?</h3>
              <p className={styles.faqAnswer}>Software engineering from entry level to senior (L3–L7 equivalent). We&apos;re adding data science, product, and design tracks soon.</p>
            </div>

            <div className={styles.faqItem}>
              <h3 className={styles.faqQuestion}>Can I use it the night before an interview?</h3>
              <p className={styles.faqAnswer}>Yes. A focused 30-minute session the night before will sharpen your answers and calm your nerves. Most users do a 3–5 day sprint before big interviews.</p>
            </div>

            <div className={styles.faqItem}>
              <h3 className={styles.faqQuestion}>What if I cancel? Do I lose my data?</h3>
              <p className={styles.faqAnswer}>No. Your session history stays in your account. You can always come back.</p>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </>
  )
}
