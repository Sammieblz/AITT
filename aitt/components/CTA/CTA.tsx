import Button from '@/components/Button/Button'
import styles from './CTA.module.css'

export default function CTA() {
  return (
    <section className={styles.section}>
      <div className={styles.container}>
        <p className={styles.overline}>Ready when you are</p>
        <h2 className={styles.heading}>
          Start your first mock interview in 60 seconds.
        </h2>
        <p className={styles.subheading}>
          No signup required. No judgment. Just practice.
        </p>
        <Button variant="volt" size="lg">
          Start practicing free
        </Button>
        <p className={styles.poweredBy}>Powered by ElevenLabs voice AI</p>
      </div>
    </section>
  )
}
