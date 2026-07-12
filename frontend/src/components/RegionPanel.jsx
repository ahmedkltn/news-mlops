import { useEffect, useState } from 'react'
import { X } from 'lucide-react'
import client from '../api/client'
import ArticleCard from './ArticleCard'
import styles from './RegionPanel.module.css'

const SENT = [
  { key: 'positive', label: 'Positif', color: 'var(--positive)' },
  { key: 'neutral', label: 'Neutre', color: 'var(--neutral)' },
  { key: 'negative', label: 'Négatif', color: 'var(--negative)' },
]

export default function RegionPanel({ region, onArticle, onClose }) {
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!region) return
    setLoading(true)
    const q = region.slug || 'national'
    client.get('/articles/', { params: { region: q, limit: 8 } })
      .then(r => setArticles(r.data || []))
      .catch(() => setArticles([]))
      .finally(() => setLoading(false))
  }, [region])

  if (!region) return null

  const s = region.sentiments || { positive: 0, neutral: 0, negative: 0 }
  const total = region.count || 0

  return (
    <aside className={styles.panel} aria-label={`Actualités — ${region.label}`}>
      <div className={styles.head}>
        <div>
          <div className={styles.kicker}>Gouvernorat</div>
          <h2 className={styles.title}>{region.label}</h2>
          <div className={styles.count}>{total} article{total > 1 ? 's' : ''}</div>
        </div>
        <button className={styles.close} onClick={onClose} aria-label="Fermer">
          <X size={18} />
        </button>
      </div>

      {total > 0 && (
        <div className={styles.sentiment}>
          <div className={styles.bar}>
            {SENT.map(x => {
              const w = total ? (s[x.key] / total) * 100 : 0
              return w > 0 ? (
                <span key={x.key} style={{ width: `${w}%`, background: x.color }} title={`${x.label} ${s[x.key]}`} />
              ) : null
            })}
          </div>
          <div className={styles.legend}>
            {SENT.map(x => (
              <span key={x.key}>
                <i style={{ background: x.color }} /> {x.label} {s[x.key]}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className={styles.list}>
        {loading ? (
          <div className={styles.empty}>Chargement…</div>
        ) : articles.length === 0 ? (
          <div className={styles.empty}>Aucun article pour ce gouvernorat.</div>
        ) : (
          articles.map(a => <ArticleCard key={a.id} article={a} onClick={onArticle} />)
        )}
      </div>
    </aside>
  )
}
