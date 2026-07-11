import { NavLink } from 'react-router-dom'
import { BookOpen, LayoutDashboard, Newspaper, Search, Zap, MessageCircle } from 'lucide-react'
import styles from './Sidebar.module.css'

const links = [
  { to: '/', label: 'Reader', icon: BookOpen },
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/articles', label: 'Articles', icon: Newspaper },
  { to: '/search', label: 'Search', icon: Search },
  { to: '/chat', label: 'Ask the news', icon: MessageCircle },
  { to: '/pipeline', label: 'Pipeline', icon: Zap },
]

export default function Sidebar() {
  return (
    <aside className={styles.sidebar}>
      <div className={styles.brand}>
        <Newspaper size={20} color="var(--accent)" />
        <span className={styles.brandText}>news-mlops</span>
      </div>
      <nav className={styles.nav}>
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `${styles.link} ${isActive ? styles.active : ''}`
            }
          >
            <Icon size={18} />
            <span className={styles.label}>{label}</span>
          </NavLink>
        ))}
      </nav>
    </aside>
  )
}
