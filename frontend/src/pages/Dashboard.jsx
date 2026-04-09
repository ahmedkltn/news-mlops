import { useEffect, useState } from 'react'
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from 'recharts'
import { Newspaper, TrendingUp, Activity } from 'lucide-react'
import client from '../api/client'
import ArticleCard from '../components/ArticleCard'
import ArticleModal from '../components/ArticleModal'
import styles from './Dashboard.module.css'

const SENTIMENT_COLORS = {
  positive: '#22c55e',
  neutral: '#64748b',
  negative: '#ef4444',
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [topics, setTopics] = useState([])
  const [recentArticles, setRecentArticles] = useState([])
  const [selectedArticle, setSelectedArticle] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [statsRes, recentRes, topicsRes] = await Promise.all([
          client.get('/articles/stats'),
          client.get('/articles/', { params: { limit: 5 } }),
          client.get('/articles/topics'),
        ])

        setStats(statsRes.data)
        setRecentArticles(recentRes.data)
        setTopics((topicsRes.data || []).slice(0, 10))
      } catch (err) {
        console.error('Dashboard load error', err)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) return <div className={styles.loading}>Loading...</div>

  return (
    <div className={styles.page}>
      <h1 className={styles.pageTitle}>Dashboard</h1>

      {/* Stat cards */}
      <div className={styles.statGrid}>
        <div className={styles.statCard}>
          <Newspaper size={20} color="var(--accent)" />
          <div>
            <div className={styles.statValue}>{stats?.total ?? '—'}</div>
            <div className={styles.statLabel}>Total Articles</div>
          </div>
        </div>
        <div className={styles.statCard}>
          <TrendingUp size={20} color="var(--positive)" />
          <div>
            <div className={styles.statValue} style={{ color: 'var(--positive)' }}>
              {stats?.sentiments.find(s => s.name === 'positive')?.value ?? 0}
            </div>
            <div className={styles.statLabel}>Positive</div>
          </div>
        </div>
        <div className={styles.statCard}>
          <Activity size={20} color="var(--negative)" />
          <div>
            <div className={styles.statValue} style={{ color: 'var(--negative)' }}>
              {stats?.sentiments.find(s => s.name === 'negative')?.value ?? 0}
            </div>
            <div className={styles.statLabel}>Negative</div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className={styles.chartsGrid}>
        <div className={styles.chartCard}>
          <h2 className={styles.chartTitle}>Sentiment Distribution</h2>
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie
                data={stats?.sentiments}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={90}
                paddingAngle={3}
                dataKey="value"
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                labelLine={false}
              >
                {stats?.sentiments.map(entry => (
                  <Cell
                    key={entry.name}
                    fill={SENTIMENT_COLORS[entry.name] || '#64748b'}
                  />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#111', border: '1px solid #222', borderRadius: 8 }}
                itemStyle={{ color: '#f1f5f9' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        <div className={styles.chartCard}>
          <h2 className={styles.chartTitle}>Top 10 Topics</h2>
          {topics.length === 0 ? (
            <div className={styles.empty}>No topics yet. Run clustering first.</div>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={topics} layout="vertical" margin={{ left: 8, right: 16 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#222" horizontal={false} />
                <XAxis type="number" tick={{ fill: '#94a3b8', fontSize: 12 }} axisLine={false} tickLine={false} />
                <YAxis
                  type="category"
                  dataKey="topic_label"
                  width={110}
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  tickFormatter={v => v && v.length > 14 ? v.slice(0, 14) + '…' : v}
                />
                <Tooltip
                  contentStyle={{ background: '#111', border: '1px solid #222', borderRadius: 8 }}
                  itemStyle={{ color: '#f1f5f9' }}
                  cursor={{ fill: 'rgba(59,130,246,0.06)' }}
                />
                <Bar dataKey="count" fill="var(--accent)" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Recent articles */}
      <div className={styles.section}>
        <h2 className={styles.sectionTitle}>Recent Articles</h2>
        <div className={styles.articleGrid}>
          {recentArticles.map(a => (
            <ArticleCard key={a.id} article={a} onClick={setSelectedArticle} />
          ))}
        </div>
      </div>

      {selectedArticle && (
        <ArticleModal article={selectedArticle} onClose={() => setSelectedArticle(null)} />
      )}
    </div>
  )
}
