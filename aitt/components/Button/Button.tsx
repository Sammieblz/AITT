import Link from 'next/link'
import styles from './Button.module.css'

type ButtonVariant = 'primary' | 'volt' | 'ghost-volt' | 'outline'
type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps {
  variant?: ButtonVariant
  size?: ButtonSize
  children: React.ReactNode
  onClick?: () => void
  className?: string
  href?: string
  fullWidth?: boolean
  disabled?: boolean
}

export default function Button({
  variant = 'primary',
  size = 'md',
  children,
  onClick,
  className = '',
  href,
  fullWidth = false,
  disabled = false,
}: ButtonProps) {
  const cls = [
    styles.base,
    styles[variant],
    styles[size],
    fullWidth ? styles.fullWidth : '',
    disabled ? styles.disabled : '',
    className,
  ].filter(Boolean).join(' ')

  if (href) {
    return (
      <Link href={href} className={cls}>
        {children}
      </Link>
    )
  }

  return (
    <button
      type="button"
      className={cls}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  )
}
