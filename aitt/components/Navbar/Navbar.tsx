'use client'

import { useState } from 'react'
import Link from 'next/link'
import Button from '@/components/Button/Button'
import styles from './Navbar.module.css'

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <header className={styles.header}>
      <nav className={styles.nav}>
        {/* Wordmark */}
        <Link href="/" className={styles.wordmark} aria-label="InterviewAI home">
          <span className={styles.wordmarkVoid}>interview</span>
          <span className={styles.wordmarkVolt}>AI</span>
        </Link>

        {/* Desktop nav links */}
        <ul className={styles.links}>
          <li><Link href="/how-it-works" className={styles.link}>How it works</Link></li>
          <li><Link href="/pricing" className={styles.link}>Pricing</Link></li>
          <li><Link href="/success-stories" className={styles.link}>Success stories</Link></li>
        </ul>

        {/* Desktop CTAs */}
        <div className={styles.ctas}>
          <Button variant="outline" size="sm" href="/get-started">Sign in</Button>
          <Button variant="volt" size="sm" href="/get-started">Start free →</Button>
        </div>

        {/* Hamburger */}
        <button
          type="button"
          className={styles.hamburger}
          aria-label={menuOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen((v) => !v)}
        >
          <span className={styles.bar} />
          <span className={styles.bar} />
          <span className={styles.bar} />
        </button>
      </nav>

      {/* Mobile dropdown */}
      {menuOpen && (
        <div className={styles.mobileMenu}>
          <ul className={styles.mobileLinks}>
            <li>
              <Link href="/how-it-works" className={styles.mobileLink} onClick={() => setMenuOpen(false)}>
                How it works
              </Link>
            </li>
            <li>
              <Link href="/pricing" className={styles.mobileLink} onClick={() => setMenuOpen(false)}>
                Pricing
              </Link>
            </li>
            <li>
              <Link href="/success-stories" className={styles.mobileLink} onClick={() => setMenuOpen(false)}>
                Success stories
              </Link>
            </li>
          </ul>
          <div className={styles.mobileCtas}>
            <Button variant="outline" size="sm" href="/get-started">Sign in</Button>
            <Button variant="volt" size="sm" href="/get-started">Start free →</Button>
          </div>
        </div>
      )}
    </header>
  )
}
