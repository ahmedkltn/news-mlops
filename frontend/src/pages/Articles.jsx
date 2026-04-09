import { useEffect, useState, useCallback } from 'react'
import { ChevronLeft, ChevronRight, SlidersHorizontal } from 'lucide-react'
import client from '../api/client'
import ArticleCard from '../components/ArticleCard'
import ArticleModal from '../components/ArticleModal'
import styles from './Articles.module.css'

const PAGE_SIZE = 20

const SENTIMENTS = ['', 'positive', 'neutral', 'negative']

export default function Articles() {
  const [articles, setArticles] = useState([])
  const [topics, setTopics] = useState([])
  const [filters, setFilters] = useState({ source: '', sentiment: '', topic_id: '' })
  const [page, setPage] = useState(0)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [selectedArticle, setSelectedArticle] = useState(null)

  useEffect(() => {
    client.get('/articles/topics').then(r => setTopics(r.data || [])).catch(() => {})
  }, [])

  const fetchArticles = useCallback(async () => {
    setLoading(true)
    try {
      const params = {
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
        ...(filters.source && { source: filters.source }),
        ...(filters.sentiment && { sentiment: filters.sentiment }),
        ...(filters.topic_id && { topic_id: filters.topic_id }),
      }
      const res = await client.get('/articles/', { params })
      setArticles(res.data)
      // If backend doesn't return total, estimate from results
      if (res.data.length === PAGE_SIZE) {
        setTotal((page + 2) * PAGE_SIZE)
      } else {
        setTotal(page * PAGE_SIZE + res.data.length)
      }
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [filters, page])

  useEffect(() => {
    fetchArticles()
  }, [fetchArticles])

  function handleFilterChange(key, value) {
    setFilters(f => ({ ...f, [key]: value }))
    setPage(0)
  }

  const totalPages = Math.ceil(total / PAGE_SIZE)

  return (
    <div className={styles.page}>
      <div className={styles.header}>
        <h1 className={styles.pageTitle}>Articles</h1>
      </div>

      {/* Filters */}
      <div className={styles.filterBar}>
        <SlidersHorizontal size={16} color="var(--text-muted)" />
        <select
          className={styles.select}
          value={filters.sentiment}
          onChange={e => handleFilterChange('sentiment', e.target.value)}
        >
          <option value="">All sentiments</option>
          {SENTIMENTS.filter(Boolean).map(s => (
            <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
          ))}
        </select>

        <select
          className={styles.select}
          value={filters.topic_id}
          onChange={e => handleFilterChange('topic_id', e.target.value)}
        >
          <option value="">All topics</option>
          {topics.map(t => (
            <option key={t.topic_id} value={t.topic_id}>{t.label || `Topic ${t.topic_id}`}</option>
          ))}
        </select>

        <input
          className={styles.input}
          placeholder="Filter by source..."
          value={filters.source}
          onChange={e => handleFilterChange('source', e.target.value)}
        />
      </div>

      {/* Grid */}
      {loading ? (
        <div className={styles.loading}>Loading articles...</div>
      ) : articles.length === 0 ? (
        <div className={styles.empty}>No articles found.</div>
      ) : (
        <div className={styles.grid}>
          {articles.map(a => (
            <ArticleCard key={a.id} article={a} onClick={setSelectedArticle} />
          ))}
        </div>
      )}

      {/* Pagination */}
      {!loading && total > PAGE_SIZE && (
        <div className={styles.pagination}>
          <button
            className={styles.pageBtn}
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
          >
            <ChevronLeft size={16} />
          </button>
          <span className={styles.pageInfo}>
            Page {page + 1}
          </span>
          <button
            className={styles.pageBtn}
            onClick={() => setPage(p => p + 1)}
            disabled={articles.length < PAGE_SIZE}
          >
            <ChevronRight size={16} />
          </button>
        </div>
      )}

      {selectedArticle && (
        <ArticleModal article={selectedArticle} onClose={() => setSelectedArticle(null)} />
      )}
    </div>
  )
}
