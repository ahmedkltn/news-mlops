import { useState } from 'react'
import { ImageOff } from 'lucide-react'
import SentimentBadge from './SentimentBadge'
import styles from './HeroCard.module.css'

function formatDate(str) {
  if (!str) return '—'
  return new Date(str).toLocaleDateString('fr-TN', {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}

export default function HeroCard({ article, onClick }) {
  const [imgFailed, setImgFailed] = useState(false)
  const showImage = article.image_url && !imgFailed

  return (
    <div className={styles.hero} onClick={() => onClick(article)}>
      {showImage ? (
        <img
          src={article.image_url}
          alt=""
          className={styles.image}
          onError={() => setImgFailed(true)}
        />
      ) : (
        <div className={styles.placeholder}>
          <ImageOff size={28} />
        </div>
      )}

      <div className={styles.content}>
        <div className={styles.top}>
          <SentimentBadge sentiment={article.sentiment} />
          {article.topic_label && (
            <span className={styles.topic}>{article.topic_label}</span>
          )}
        </div>
        <h1 className={styles.title}>{article.title}</h1>
        <div className={styles.footer}>
          <span className={styles.source}>{article.source}</span>
          <span className={styles.date}>
            {formatDate(article.published_at || article.scraped_at)}
          </span>
        </div>
      </div>
    </div>
  )
}
