import styles from './Badge.module.css'

type BadgeVariant = 'volt' | 'alert' | 'black' | 'white' | 'outline'

interface BadgeProps {
  variant?: BadgeVariant
  children: React.ReactNode
  className?: string
}

export default function Badge({
  variant = 'volt',
  children,
  className = '',
}: BadgeProps) {
  const cls = [styles.base, styles[variant], className].filter(Boolean).join(' ')

  return <span className={cls}>{children}</span>
}
