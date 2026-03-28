import Link from 'next/link'
import styles from './Footer.module.css'

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.inner}>
        <div className={styles.grid}>
          {/* Column 1: Brand */}
          <div className={styles.col}>
            <div className={styles.wordmark}>
              <span className={styles.wordmarkWhite}>interview</span>
              <span className={styles.wordmarkVolt}>AI</span>
            </div>
            <p className={styles.tagline}>Stop guessing. Start acing.</p>
            <p className={styles.description}>AI-powered behavioral interview coaching for software engineers.</p>
          </div>

          {/* Column 2: Product */}
          <div className={styles.col}>
            <p className={styles.colLabel}>Product</p>
            <ul className={styles.colLinks}>
              <li><Link href="/how-it-works" className={styles.colLink}>How it works</Link></li>
              <li><Link href="/pricing" className={styles.colLink}>Pricing</Link></li>
              <li><Link href="/success-stories" className={styles.colLink}>Success stories</Link></li>
              <li><Link href="/get-started" className={styles.colLink}>Get started</Link></li>
            </ul>
          </div>

          {/* Column 3: Company */}
          <div className={styles.col}>
            <p className={styles.colLabel}>Company</p>
            <ul className={styles.colLinks}>
              <li><Link href="/about" className={styles.colLink}>About</Link></li>
              <li><Link href="/blog" className={styles.colLink}>Blog</Link></li>
              <li><Link href="/contact" className={styles.colLink}>Contact</Link></li>
              <li><Link href="/privacy" className={styles.colLink}>Privacy policy</Link></li>
            </ul>
          </div>
        </div>

        <div className={styles.bottom}>
          <p className={styles.copyright}>© 2026 InterviewAI. All rights reserved.</p>
          <p className={styles.powered}>Powered by ElevenLabs voice AI</p>
        </div>
      </div>
    </footer>
  )
}
