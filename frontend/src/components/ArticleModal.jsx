import { useEffect } from 'react'
import { X, ExternalLink } from 'lucide-react'
import SentimentBadge from './SentimentBadge'
import styles from './ArticleModal.module.css'

function formatDate(str) {
  if (!str) return '—'
  return new Date(str).toLocaleDateString('fr-TN', {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}

export default function ArticleModal({ article, onClose }) {
  useEffect(() => {
    const handler = (e) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', handler)
    return () => document.removeEventListener('keydown', handler)
  }, [onClose])

  if (!article) return null

  return (
    <div className={styles.overlay} onClick={onClose}>
      <div className={styles.modal} onClick={(e) => e.stopPropagation()}>
        <div className={styles.header}>
          <h2 className={styles.title}>{article.title}</h2>
          <button className={styles.closeBtn} onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        <div className={styles.meta}>
          <SentimentBadge sentiment={article.sentiment} />
          <span className={styles.metaItem}>{article.source}</span>
          {article.topic_label && (
            <span className={styles.topic}>{article.topic_label}</span>
          )}
          <span className={styles.metaItem}>{formatDate(article.scraped_at)}</span>
        </div>

        <div className={styles.content}>
          {article.content || 'No content available.'}
        </div>

        {article.url && (
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.externalLink}
          >
            <ExternalLink size={14} />
            Open original article
          </a>
        )}
      </div>
    </div>
  )
}
