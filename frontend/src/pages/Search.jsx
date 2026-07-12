import { useState, useRef } from 'react'
import { Search as SearchIcon, Loader2 } from 'lucide-react'
import client from '../api/client'
import SentimentBadge from '../components/SentimentBadge'
import ArticleModal from '../components/ArticleModal'
import PageHeader from '../components/PageHeader'
import styles from './Search.module.css'

export default function Search() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [searched, setSearched] = useState(false)
  const [loading, setLoading] = useState(false)
  const [selectedArticle, setSelectedArticle] = useState(null)
  const inputRef = useRef()

  async function handleSearch(e) {
    e.preventDefault()
    if (!query.trim()) return
    setLoading(true)
    setSearched(true)
    try {
      const res = await client.get('/search/', { params: { q: query.trim(), limit: 20 } })
      setResults(res.data || [])
    } catch (err) {
      console.error(err)
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.page}>
      <PageHeader
        title="Recherche"
        subtitle="Trouvez des articles par sujet, événement ou mot-clé à travers toutes les sources."
      />

      <form className={styles.searchForm} onSubmit={handleSearch}>
        <div className={styles.inputWrapper}>
          <SearchIcon size={18} className={styles.searchIcon} />
          <input
            ref={inputRef}
            className={styles.input}
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Rechercher un sujet, un événement, un concept…"
            autoFocus
          />
        </div>
        <button type="submit" className={styles.searchBtn} disabled={loading || !query.trim()}>
          {loading ? <Loader2 size={16} className={styles.spin} /> : 'Rechercher'}
        </button>
      </form>

      {loading && (
        <div className={styles.loading}>Recherche en cours…</div>
      )}

      {!loading && searched && results.length === 0 && (
        <div className={styles.empty}>Aucun résultat pour «&nbsp;{query}&nbsp;».</div>
      )}

      {!loading && results.length > 0 && (
        <div className={styles.results}>
          <div className={styles.resultsCount}>{results.length} résultat{results.length > 1 ? 's' : ''}</div>
          {results.map((item, i) => {
            const article = item.article || item
            const score = item.score ?? item.similarity ?? null
            return (
              <div
                key={article.id || i}
                className={styles.resultCard}
                onClick={() => setSelectedArticle(article)}
              >
                <div className={styles.resultTop}>
                  <div className={styles.resultMeta}>
                    <SentimentBadge sentiment={article.sentiment} />
                    <span className={styles.source}>{article.source}</span>
                  </div>
                  {score !== null && (
                    <span className={styles.score}>{(score * 100).toFixed(1)}%</span>
                  )}
                </div>
                <h3 className={styles.resultTitle}>{article.title}</h3>
                {score !== null && (
                  <div className={styles.progressBar}>
                    <div
                      className={styles.progressFill}
                      style={{ width: `${(score * 100).toFixed(1)}%` }}
                    />
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {selectedArticle && (
        <ArticleModal article={selectedArticle} onClose={() => setSelectedArticle(null)} />
      )}
    </div>
  )
}
