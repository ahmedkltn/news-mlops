import { useState } from 'react'
import SentimentBadge from './SentimentBadge'
import styles from './ArticleCard.module.css'

function formatDate(str) {
  if (!str) return '—'
  return new Date(str).toLocaleDateString('fr-TN', {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}

export default function ArticleCard({ article, onClick }) {
  const [imgFailed, setImgFailed] = useState(false)

  return (
    <div className={styles.card} onClick={() => onClick(article)}>
      {article.image_url && !imgFailed && (
        <img
          src={article.image_url}
          alt=""
          className={styles.image}
          loading="lazy"
          onError={() => setImgFailed(true)}
        />
      )}
      <div className={styles.top}>
        <SentimentBadge sentiment={article.sentiment} />
        {article.topic_label && (
          <span className={styles.topic}>{article.topic_label}</span>
        )}
      </div>
      <h3 className={styles.title}>{article.title}</h3>
      <div className={styles.footer}>
        <span className={styles.source}>{article.source}</span>
        <span className={styles.date}>{formatDate(article.scraped_at)}</span>
      </div>
    </div>
  )
}
