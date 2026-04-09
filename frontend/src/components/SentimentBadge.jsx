import styles from './SentimentBadge.module.css'

export default function SentimentBadge({ sentiment }) {
  if (!sentiment) return null
  return (
    <span className={`${styles.badge} ${styles[sentiment]}`}>
      {sentiment}
    </span>
  )
}
