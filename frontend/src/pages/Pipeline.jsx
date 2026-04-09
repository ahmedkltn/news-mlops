import { useState } from 'react'
import { Play, GitMerge, CheckCircle, XCircle } from 'lucide-react'
import client from '../api/client'
import ConfirmDialog from '../components/ConfirmDialog'
import styles from './Pipeline.module.css'

function StatusMessage({ status }) {
  if (!status) return null
  const isError = status.type === 'error'
  return (
    <div className={`${styles.statusMsg} ${isError ? styles.error : styles.success}`}>
      {isError ? <XCircle size={16} /> : <CheckCircle size={16} />}
      <span>{status.text}</span>
    </div>
  )
}

export default function Pipeline() {
  const [maxPages, setMaxPages] = useState(5)
  const [confirm, setConfirm] = useState(null) // { action, title, message }
  const [loading, setLoading] = useState({ scrape: false, cluster: false })
  const [status, setStatus] = useState({ scrape: null, cluster: null })

  function handleScrapeClick() {
    setConfirm({
      action: 'scrape',
      title: 'Trigger Scraping Pipeline',
      message: `This will scrape up to ${maxPages} pages from Kapitalis and run the full ETL pipeline. Continue?`,
    })
  }

  function handleClusterClick() {
    setConfirm({
      action: 'cluster',
      title: 'Run BERTopic Clustering',
      message: 'This will re-run BERTopic clustering on all stored articles and update topic assignments. Continue?',
    })
  }

  async function handleConfirm() {
    const action = confirm.action
    setConfirm(null)
    setLoading(l => ({ ...l, [action]: true }))
    setStatus(s => ({ ...s, [action]: null }))

    try {
      if (action === 'scrape') {
        const res = await client.post('/pipeline/trigger', null, { params: { max_pages: maxPages } })
        setStatus(s => ({ ...s, scrape: { type: 'success', text: res.data?.message || 'Pipeline triggered successfully.' } }))
      } else {
        const res = await client.post('/pipeline/cluster')
        setStatus(s => ({ ...s, cluster: { type: 'success', text: res.data?.message || 'Clustering completed successfully.' } }))
      }
    } catch (err) {
      const text = err.response?.data?.detail || err.message || 'An error occurred.'
      setStatus(s => ({ ...s, [action]: { type: 'error', text } }))
    } finally {
      setLoading(l => ({ ...l, [action]: false }))
    }
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.pageTitle}>Pipeline</h1>
      <p className={styles.subtitle}>Trigger data ingestion and model operations</p>

      <div className={styles.grid}>
        {/* Scraping card */}
        <div className={styles.card}>
          <div className={styles.cardIcon} style={{ background: 'rgba(59,130,246,0.1)' }}>
            <Play size={24} color="var(--accent)" />
          </div>
          <h2 className={styles.cardTitle}>Trigger Scraping</h2>
          <p className={styles.cardDesc}>
            Scrapes Tunisian news articles from Kapitalis and runs the full ETL pipeline
            including embedding generation and sentiment analysis.
          </p>

          <div className={styles.field}>
            <label className={styles.label}>Max pages to scrape</label>
            <input
              type="number"
              className={styles.numberInput}
              value={maxPages}
              min={1}
              max={50}
              onChange={e => setMaxPages(Number(e.target.value))}
            />
          </div>

          <StatusMessage status={status.scrape} />

          <button
            className={styles.actionBtn}
            onClick={handleScrapeClick}
            disabled={loading.scrape}
          >
            {loading.scrape ? 'Running...' : 'Run Scraping Pipeline'}
          </button>
        </div>

        {/* Clustering card */}
        <div className={styles.card}>
          <div className={styles.cardIcon} style={{ background: 'rgba(34,197,94,0.1)' }}>
            <GitMerge size={24} color="var(--positive)" />
          </div>
          <h2 className={styles.cardTitle}>Run Clustering</h2>
          <p className={styles.cardDesc}>
            Runs BERTopic clustering on all stored articles to discover and assign
            topic clusters. Updates topic labels for all articles.
          </p>

          <StatusMessage status={status.cluster} />

          <button
            className={`${styles.actionBtn} ${styles.clusterBtn}`}
            onClick={handleClusterClick}
            disabled={loading.cluster}
          >
            {loading.cluster ? 'Running...' : 'Run BERTopic Clustering'}
          </button>
        </div>
      </div>

      {confirm && (
        <ConfirmDialog
          title={confirm.title}
          message={confirm.message}
          onConfirm={handleConfirm}
          onCancel={() => setConfirm(null)}
        />
      )}
    </div>
  )
}
