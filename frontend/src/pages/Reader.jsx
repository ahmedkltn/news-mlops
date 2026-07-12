import { useEffect, useMemo, useState } from 'react'
import client from '../api/client'
import ArticleCard from '../components/ArticleCard'
import ArticleModal from '../components/ArticleModal'
import HeroCard from '../components/HeroCard'
import styles from './Reader.module.css'

const ALL_TAB = 'Toutes'

export default function Reader() {
  const [articles, setArticles] = useState([])
  const [loading, setLoading] = useState(true)
  const [selectedArticle, setSelectedArticle] = useState(null)
  const [activeTab, setActiveTab] = useState(ALL_TAB)

  useEffect(() => {
    async function load() {
      try {
        const res = await client.get('/articles/', { params: { limit: 21 } })
        setArticles(res.data || [])
      } catch (err) {
        console.error('Reader load error', err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  const heroArticle = articles[0]
  const restArticles = useMemo(() => articles.slice(1), [articles])

  const tabs = useMemo(() => {
    const sources = [...new Set(articles.map(a => a.source).filter(Boolean))]
    return [ALL_TAB, ...sources]
  }, [articles])

  const gridArticles = useMemo(() => {
    if (activeTab === ALL_TAB) return restArticles
    return restArticles.filter(a => a.source === activeTab)
  }, [restArticles, activeTab])

  if (loading) {
    return (
      <div className={styles.page}>
        <div className={styles.skeletonHero} />
        <div className={styles.grid}>
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className={styles.skeletonCard} />
          ))}
        </div>
      </div>
    )
  }

  if (articles.length === 0) {
    return (
      <div className={styles.page}>
        <div className={styles.empty}>
          <h2 className={styles.emptyTitle}>Aucun article pour le moment</h2>
          <p>Lancez le pipeline pour récupérer les dernières actualités.</p>
        </div>
      </div>
    )
  }

  return (
    <div className={styles.page}>
      {heroArticle && <HeroCard article={heroArticle} onClick={setSelectedArticle} />}

      <div className={styles.sectionHead}>
        <h2 className={styles.sectionTitle}>Dernières actualités</h2>
        <div className={styles.filters}>
          {tabs.map(tab => (
            <button
              key={tab}
              className={`${styles.chip} ${activeTab === tab ? styles.chipActive : ''}`}
              onClick={() => setActiveTab(tab)}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {gridArticles.length === 0 ? (
        <div className={styles.empty}>Aucun article pour cette source.</div>
      ) : (
        <div className={styles.grid}>
          {gridArticles.map(a => (
            <ArticleCard key={a.id} article={a} onClick={setSelectedArticle} />
          ))}
        </div>
      )}

      {selectedArticle && (
        <ArticleModal article={selectedArticle} onClose={() => setSelectedArticle(null)} />
      )}
    </div>
  )
}
