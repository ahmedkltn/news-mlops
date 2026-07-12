import styles from './SentimentBadge.module.css'

const LABELS = {
  positive: 'Positif',
  neutral: 'Neutre',
  negative: 'Négatif',
}

/**
 * variant="pill" — filled chip (hero, modal)
 * variant="dot"  — subtle dot + label (cards, meta rows)
 */
export default function SentimentBadge({ sentiment, variant = 'pill' }) {
  if (!sentiment) return null
  const label = LABELS[sentiment] || sentiment

  if (variant === 'dot') {
    return (
      <span className={styles.dotWrap}>
        <span className={`${styles.dot} ${styles[sentiment]}`} aria-hidden="true" />
        <span className={styles.dotLabel}>{label}</span>
      </span>
    )
  }

  return (
    <span className={`${styles.badge} ${styles[sentiment]}`}>{label}</span>
  )
}
