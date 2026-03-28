import styles from './ScoreIndicator.module.css'

type Score = 1 | 2 | 3 | 4 | 5

interface ScoreIndicatorProps {
  score: Score
  className?: string
}

export default function ScoreIndicator({ score, className = '' }: ScoreIndicatorProps) {
  const cls = [styles.tile, styles[`score${score}`], className].filter(Boolean).join(' ')

  return (
    <div className={cls} aria-label={`Score ${score} out of 5`}>
      {score}
    </div>
  )
}
