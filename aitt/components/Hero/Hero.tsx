import Badge from '@/components/Badge/Badge'
import Button from '@/components/Button/Button'
import styles from './Hero.module.css'

export default function Hero() {
  return (
    <section className={styles.section}>
      {/* Ghost "AI" decorative text rendered via ::after in CSS */}

      {/* Absolute-positioned badge top-right */}
      <div className={styles.badgeWrapper}>
        <Badge variant="outline" className={styles.hacksuBadge}>
          HacKSU 2026
        </Badge>
      </div>

      {/* Centered content */}
      <div className={styles.content}>
        {/* Hero wordmark */}
        <div className={styles.heroWordmark} aria-label="interviewAI">
          <span className={styles.heroWordmarkWhite}>interview</span>
          <span className={styles.heroWordmarkVolt}>AI</span>
        </div>

        <h1 className={styles.heading}>
          Stop guessing. Start acing.
        </h1>
        <p className={styles.subheading}>
          Real-time AI voice coaching built for software engineers. No fluff. Just results.
        </p>
        <div className={styles.actions}>
          <Button variant="volt" size="md">Start practicing</Button>
          <Button variant="outline" size="md" className={styles.outlineOverride}>
            See how it works
          </Button>
        </div>
      </div>
    </section>
  )
}
