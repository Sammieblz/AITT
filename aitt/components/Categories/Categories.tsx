import Badge from '@/components/Badge/Badge'
import styles from './Categories.module.css'

type BadgeVariant = 'volt' | 'alert' | 'black' | 'white' | 'outline'

const categories: { label: string; variant: BadgeVariant }[] = [
  { label: 'Leadership', variant: 'volt' },
  { label: 'Conflict', variant: 'volt' },
  { label: 'Problem solving', variant: 'volt' },
  { label: 'Failure & resilience', variant: 'alert' },
  { label: 'Achievement', variant: 'volt' },
  { label: 'Adaptability', variant: 'volt' },
  { label: 'Senior SWE track', variant: 'black' },
  { label: 'STAR method', variant: 'white' },
]

export default function Categories() {
  return (
    <section id="categories" className={styles.section}>
      <div className={styles.container}>
        <p className={styles.label}>Question categories</p>
        <h2 className={styles.heading}>Practice across every dimension.</h2>

        <div className={styles.badgeRow}>
          {categories.map((cat) => (
            <Badge key={cat.label} variant={cat.variant}>
              {cat.label}
            </Badge>
          ))}
        </div>

        <p className={styles.body}>
          From leadership and conflict to technical judgment and failure — we cover the full behavioral interview spectrum for software engineers.
        </p>
      </div>
    </section>
  )
}
