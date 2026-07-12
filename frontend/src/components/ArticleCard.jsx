import { useState } from 'react'
import { ImageOff } from 'lucide-react'
import SentimentBadge from './SentimentBadge'
import { relativeTime } from '../utils/time'
import { proxied } from '../utils/image'
import styles from './ArticleCard.module.css'

export default function ArticleCard({ article, onClick }) {
  const [imgFailed, setImgFailed] = useState(false)
  const showImage = article.image_url && !imgFailed
  const kicker = article.topic_label || article.source

  return (
    <article className={styles.card} onClick={() => onClick(article)}>
      <div className={styles.media}>
        {showImage ? (
          <img
            src={proxied(article.image_url)}
            alt=""
            className={styles.image}
            loading="lazy"
            onError={() => setImgFailed(true)}
          />
        ) : (
          <div className={styles.placeholder}>
            <ImageOff size={22} />
          </div>
        )}
      </div>

      <div className={styles.body}>
        {kicker && <span className={styles.kicker}>{kicker}</span>}
        <h3 className={styles.title}>{article.title}</h3>
        <div className={styles.meta}>
          <span className={styles.source}>{article.source}</span>
          <span className={styles.sep} aria-hidden="true">·</span>
          <span>{relativeTime(article.published_at || article.scraped_at)}</span>
          {article.sentiment && (
            <SentimentBadge sentiment={article.sentiment} variant="dot" />
          )}
        </div>
      </div>
    </article>
  )
}
