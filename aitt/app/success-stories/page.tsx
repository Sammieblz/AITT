import Navbar from '@/components/Navbar/Navbar'
import Footer from '@/components/Footer/Footer'
import Button from '@/components/Button/Button'
import Badge from '@/components/Badge/Badge'
import { testimonials, stats, companies } from '@/lib/mockData'
import styles from './page.module.css'

export default function SuccessStories() {
  return (
    <>
      <Navbar />
      <main>
        {/* ── Hero ──────────────────────────────────────────────────────── */}
        <section className={styles.hero}>
          <div className={styles.heroInner}>
            <Badge variant="volt" className={styles.heroBadge}>Real results</Badge>
            <h1 className={styles.heroHeadline}>
              2,400+ engineers.<br />Dozens of offers.<br />One tool.
            </h1>
            <p className={styles.heroSub}>
              These are real people who practiced, got coached, and landed jobs they wanted. You could be next.
            </p>
          </div>
        </section>

        {/* ── Stats Strip ───────────────────────────────────────────────── */}
        <section className={styles.statsStrip}>
          <div className={styles.statsInner}>
            {stats.map((stat) => (
              <div key={stat.label} className={styles.statBlock}>
                <div className={styles.statValue}>{stat.value}</div>
                <div className={styles.statLabel}>{stat.label}</div>
              </div>
            ))}
          </div>
        </section>

        {/* ── Testimonials ──────────────────────────────────────────────── */}
        <section className={styles.testimonials}>
          <div className={styles.testimonialsInner}>
            <div className={styles.testimonialGrid}>
              {testimonials.map((t) => (
                <div key={t.id} className={styles.testimonialCard}>
                  <div className={styles.stars}>★★★★★</div>
                  <p className={styles.quote}>{t.quote}</p>
                  <div className={styles.cardFooter}>
                    <span className={styles.name}>{t.name}</span>
                    <Badge variant={t.badgeVariant}>{t.badge}</Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Companies ─────────────────────────────────────────────────── */}
        <section className={styles.companies}>
          <div className={styles.companiesInner}>
            <h2 className={styles.companiesHeadline}>Our users have landed offers at</h2>
            <div className={styles.companiesList}>
              {companies.map((company) => (
                <span key={company} className={styles.companyName}>{company}</span>
              ))}
            </div>
          </div>
        </section>

        {/* ── Bottom CTA ────────────────────────────────────────────────── */}
        <section className={styles.cta}>
          <div className={styles.ctaInner}>
            <h2 className={styles.ctaHeadline}>
              You could be the next one<br />on this page.
            </h2>
            <p className={styles.ctaSub}>It starts with one 20-minute session.</p>
            <Button variant="primary" size="lg" href="/get-started">
              Start free — no card needed →
            </Button>
          </div>
        </section>
      </main>
      <Footer />
    </>
  )
}
