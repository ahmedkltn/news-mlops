import { useMemo, useState } from 'react'
import { geoIdentity, geoPath } from 'd3-geo'
import geojson from '../assets/tunisia-governorates.json'
import styles from './RegionMap.module.css'

const W = 480
const H = 760

const SENT_COLOR = {
  positive: '#16a34a',
  neutral: '#94a3b8',
  negative: '#ef4444',
}

export default function RegionMap({ data, metric, selected, onSelect }) {
  const [hover, setHover] = useState(null) // { name, count, dominant, x, y }

  const { paths, byslug, maxCount } = useMemo(() => {
    // geoIdentity (planar) — winding-agnostic, unlike geoMercator which
    // treats geoBoundaries' ring order as the globe's complement and
    // collapses the map. reflectY flips lat (screen Y grows downward).
    const projection = geoIdentity().reflectY(true).fitSize([W, H], geojson)
    const path = geoPath(projection)
    const paths = geojson.features.map(f => ({
      slug: f.properties.slug,
      name: f.properties.name,
      d: path(f),
    }))
    const byslug = {}
    let maxCount = 0
    for (const r of data || []) {
      if (r.region) byslug[r.region] = r
      maxCount = Math.max(maxCount, r.region ? r.count : 0)
    }
    return { paths, byslug, maxCount }
  }, [data])

  function fillFor(slug) {
    const r = byslug[slug]
    if (!r || !r.count) return 'var(--map-empty)'
    if (metric === 'sentiment') return SENT_COLOR[r.dominant] || 'var(--map-empty)'
    // volume: brand-red, alpha scaled by count
    const a = 0.18 + 0.72 * (r.count / (maxCount || 1))
    return `rgba(220, 38, 38, ${a.toFixed(2)})`
  }

  return (
    <div className={styles.wrap}>
      <svg viewBox={`0 0 ${W} ${H}`} className={styles.svg} role="group" aria-label="Carte des gouvernorats de Tunisie">
        {paths.map(p => {
          const r = byslug[p.slug]
          const count = r?.count || 0
          const isSel = selected === p.slug
          return (
            <path
              key={p.slug}
              d={p.d}
              className={`${styles.region} ${isSel ? styles.selected : ''}`}
              style={{ fill: fillFor(p.slug) }}
              tabIndex={0}
              role="button"
              aria-label={`${p.name} — ${count} article${count > 1 ? 's' : ''}`}
              onClick={() => onSelect(isSel ? null : p.slug)}
              onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(isSel ? null : p.slug) } }}
              onMouseMove={e => setHover({ name: p.name, count, dominant: r?.dominant, x: e.clientX, y: e.clientY })}
              onMouseLeave={() => setHover(null)}
            />
          )
        })}
      </svg>

      {hover && (
        <div className={styles.tooltip} style={{ left: hover.x + 14, top: hover.y + 14 }}>
          <strong>{hover.name}</strong>
          <span>{hover.count} article{hover.count > 1 ? 's' : ''}</span>
        </div>
      )}
    </div>
  )
}
