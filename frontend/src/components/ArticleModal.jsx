import { useEffect, useState } from 'react'
import { X, ExternalLink, Sparkles } from 'lucide-react'
import client from '../api/client'
import SentimentBadge from './SentimentBadge'
import styles from './ArticleModal.module.css'

function formatDate(str) {
  if (!str) return '—'
  return new Date(str).toLocaleDateString('fr-TN', {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}

// Keyed by article id from the parent so state resets naturally on remount
// instead of requiring a synchronous setState reset inside an effect.
function ArticleSummary({ articleId }) {
  const [summary, setSummary] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    client.get(`/genai/summary/${articleId}`)
      .then(res => {
        if (!cancelled) setSummary(res.data?.summary || '')
      })
      .catch(err => {
        console.error('Summary fetch error', err)
        if (!cancelled) setSummary('')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => { cancelled = true }
  }, [articleId])

  if (!loading && !summary) return null

  return (
    <div className={styles.summaryBox}>
      <div className={styles.summaryLabel}>
        <Sparkles size={13} />
        Résumé
      </div>
      <div className={styles.summaryText}>
        {loading ? 'Résumé…' : summary}
      </div>
    </div>
  )
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
          <button className={styles.closeBtn} onClick={onClose} aria-label="Fermer">
            <X size={18} />
          </button>
        </div>

        <div className={styles.meta}>
          <SentimentBadge sentiment={article.sentiment} />
          <span className={styles.metaItem}>{article.source}</span>
          {article.topic_label && (
            <span className={styles.topic}>{article.topic_label}</span>
          )}
          <span className={styles.metaItem}>{formatDate(article.published_at || article.scraped_at)}</span>
        </div>

        {article.id != null && <ArticleSummary key={article.id} articleId={article.id} />}

        <div className={styles.content}>
          {article.content || 'Contenu non disponible.'}
        </div>

        {article.url && (
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className={styles.externalLink}
          >
            <ExternalLink size={14} />
            Lire l'article original
          </a>
        )}
      </div>
    </div>
  )
}
