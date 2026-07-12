import { NavLink } from 'react-router-dom'
import { Flame, Newspaper, Search, Sparkles, BarChart3, Map, Zap } from 'lucide-react'
import { todayLong } from '../utils/time'
import styles from './Masthead.module.css'

const links = [
  { to: '/', label: 'À la une', icon: Flame, end: true },
  { to: '/articles', label: 'Articles', icon: Newspaper },
  { to: '/carte', label: 'Carte', icon: Map },
  { to: '/search', label: 'Recherche', icon: Search },
  { to: '/chat', label: 'Assistant IA', icon: Sparkles },
  { to: '/dashboard', label: 'Analyses', icon: BarChart3 },
]

export default function Masthead() {
  return (
    <header className={styles.masthead}>
      <div className={styles.topBar}>
        <NavLink to="/" className={styles.brand} aria-label="Tuniscope — accueil">
          <span className={styles.brandMark}>Tuni</span>scope
          <span className={styles.brandDot} />
        </NavLink>

        <div className={styles.right}>
          <time className={styles.date}>{todayLong()}</time>
          <NavLink
            to="/pipeline"
            className={({ isActive }) => `${styles.pipeline} ${isActive ? styles.pipelineActive : ''}`}
            aria-label="Pipeline de données"
            title="Pipeline de données"
          >
            <Zap size={16} />
          </NavLink>
        </div>
      </div>

      <nav className={styles.nav} aria-label="Sections">
        <div className={styles.navInner}>
          {links.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) => `${styles.link} ${isActive ? styles.active : ''}`}
            >
              <Icon size={16} className={styles.icon} />
              <span>{label}</span>
            </NavLink>
          ))}
        </div>
      </nav>
    </header>
  )
}
