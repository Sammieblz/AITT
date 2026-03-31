import styles from './Features.module.css'

const features = [
  {
    id: 'voice',
    iconBg: '#1A3300',
    icon: (
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
        {/* Mic body — stroked in Volt */}
        <rect x="7.5" y="1.5" width="7" height="11" rx="3.5" stroke="#B4FF5B" strokeWidth="1.5" />
        {/* Mic stand arc */}
        <path
          d="M4.5 11C4.5 14.59 7.41 17.5 11 17.5s6.5-2.91 6.5-6.5"
          stroke="#B4FF5B"
          strokeWidth="1.5"
          strokeLinecap="round"
        />
        {/* Stem */}
        <line x1="11" y1="17.5" x2="11" y2="20.5" stroke="#B4FF5B" strokeWidth="1.5" strokeLinecap="round" />
        {/* Base */}
        <line x1="7.5" y1="20.5" x2="14.5" y2="20.5" stroke="#B4FF5B" strokeWidth="1.5" strokeLinecap="round" />
      </svg>
    ),
    heading: 'Real-time voice coaching',
    body: 'Speak your answers out loud and get instant AI feedback — just like a real interview.',
  },
  {
    id: 'star',
    iconBg: '#1A1A1A',
    icon: (
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
        <rect x="2" y="2" width="8" height="8" rx="1.5" fill="#FF8800" />
        <rect x="12" y="2" width="8" height="8" rx="1.5" fill="#FF8800" />
        <rect x="2" y="12" width="8" height="8" rx="1.5" fill="#FF8800" />
        <rect x="12" y="12" width="8" height="8" rx="1.5" fill="#FF8800" />
      </svg>
    ),
    heading: 'STAR method feedback',
    body: 'Every answer is scored across Situation, Task, Action, and Result so you know exactly where to improve.',
  },
  {
    id: 'role',
    iconBg: '#1A3300',
    icon: (
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
        {/* Bullseye — stroked in Volt */}
        <circle cx="11" cy="11" r="9.5" stroke="#B4FF5B" strokeWidth="1.3" />
        <circle cx="11" cy="11" r="6" stroke="#B4FF5B" strokeWidth="1.3" />
        <circle cx="11" cy="11" r="2.5" stroke="#B4FF5B" strokeWidth="1.3" />
        <circle cx="11" cy="11" r="1" fill="#B4FF5B" />
      </svg>
    ),
    heading: 'Tailored to your role',
    body: 'Pick your experience level and focus areas. AITT adapts the questions to match your track.',
  },
]

export default function Features() {
  return (
    <section id="features" className={styles.section}>
      <div className={styles.container}>
        <p className={styles.label}>Why AITT</p>
        <h2 className={styles.heading}>
          Everything you need to interview with confidence.
        </h2>

        <div className={styles.grid}>
          {features.map((f) => (
            <article key={f.id} className={styles.card}>
              <div
                className={styles.iconCircle}
                style={{ backgroundColor: f.iconBg }}
              >
                {f.icon}
              </div>
              <h3 className={styles.cardHeading}>{f.heading}</h3>
              <p className={styles.cardBody}>{f.body}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  )
}
