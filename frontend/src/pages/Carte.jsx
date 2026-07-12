import { useEffect, useMemo, useState } from 'react'
import client from '../api/client'
import PageHeader from '../components/PageHeader'
import RegionMap from '../components/RegionMap'
import RegionPanel from '../components/RegionPanel'
import ArticleModal from '../components/ArticleModal'
import geojson from '../assets/tunisia-governorates.json'
import styles from './Carte.module.css'

const NAMES = Object.fromEntries(geojson.features.map(f => [f.properties.slug, f.properties.name]))

export default function Carte() {
  const [data, setData] = useState([])
  const [loading, setLoading] = useState(true)
  const [metric, setMetric] = useState('volume')
  const [selected, setSelected] = useState(null) // slug or 'national'
  const [article, setArticle] = useState(null)

  useEffect(() => {
    client.get('/articles/regions')
      .then(r => setData(r.data || []))
      .catch(() => setData([]))
      .finally(() => setLoading(false))
  }, [])

  const byslug = useMemo(() => {
    const m = {}
    for (const r of data) m[r.region || 'national'] = r
    return m
  }, [data])

  const national = byslug['national']

  const selectedRegion = useMemo(() => {
    if (!selected) return null
    const row = byslug[selected] || { count: 0, sentiments: {} }
    return {
      slug: selected === 'national' ? null : selected,
      label: selected === 'national' ? 'National / non localisé' : (NAMES[selected] || selected),
      count: row.count,
      sentiments: row.sentiments,
    }
  }, [selected, byslug])

  return (
    <div className={styles.page}>
      <PageHeader
        title="Carte"
        subtitle="L'actualité tunisienne par gouvernorat. Cliquez une région pour explorer."
      >
        <div className={styles.toggle} role="group" aria-label="Métrique de la carte">
          <button
            className={metric === 'volume' ? styles.on : ''}
            onClick={() => setMetric('volume')}
          >Volume</button>
          <button
            className={metric === 'sentiment' ? styles.on : ''}
            onClick={() => setMetric('sentiment')}
          >Sentiment</button>
        </div>
      </PageHeader>

      {loading ? (
        <div className={styles.loading}>Chargement de la carte…</div>
      ) : (
        <div className={`${styles.layout} ${selectedRegion ? styles.split : ''}`}>
          <div className={styles.mapCol}>
            <RegionMap data={data} metric={metric} selected={selected} onSelect={setSelected} />

            <div className={styles.footerRow}>
              {metric === 'volume' ? (
                <div className={styles.legend}>
                  <span>Moins</span>
                  <i className={styles.scale} />
                  <span>Plus d'articles</span>
                </div>
              ) : (
                <div className={styles.legend}>
                  <span><i style={{ background: 'var(--positive)' }} /> Positif</span>
                  <span><i style={{ background: 'var(--neutral)' }} /> Neutre</span>
                  <span><i style={{ background: 'var(--negative)' }} /> Négatif</span>
                </div>
              )}

              {national && national.count > 0 && (
                <button
                  className={`${styles.national} ${selected === 'national' ? styles.on : ''}`}
                  onClick={() => setSelected(selected === 'national' ? null : 'national')}
                >
                  National / non localisé · {national.count}
                </button>
              )}
            </div>
          </div>

          {selectedRegion && (
            <div className={styles.panelCol}>
              <RegionPanel region={selectedRegion} onArticle={setArticle} onClose={() => setSelected(null)} />
            </div>
          )}
        </div>
      )}

      {article && <ArticleModal article={article} onClose={() => setArticle(null)} />}
    </div>
  )
}
