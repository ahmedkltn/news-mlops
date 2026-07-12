import { useState } from 'react'
import { Play, GitMerge, CheckCircle, XCircle } from 'lucide-react'
import client from '../api/client'
import ConfirmDialog from '../components/ConfirmDialog'
import PageHeader from '../components/PageHeader'
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
      title: 'Lancer la collecte',
      message: `Cela va collecter jusqu'à ${maxPages} pages de la presse tunisienne et exécuter tout le pipeline ETL. Continuer ?`,
    })
  }

  function handleClusterClick() {
    setConfirm({
      action: 'cluster',
      title: 'Lancer le regroupement thématique',
      message: 'Cela va relancer le clustering BERTopic sur tous les articles et mettre à jour les thèmes. Continuer ?',
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
        setStatus(s => ({ ...s, scrape: { type: 'success', text: res.data?.message || 'Pipeline lancé avec succès.' } }))
      } else {
        const res = await client.post('/pipeline/cluster')
        setStatus(s => ({ ...s, cluster: { type: 'success', text: res.data?.message || 'Clustering terminé avec succès.' } }))
      }
    } catch (err) {
      const text = err.response?.data?.detail || err.message || 'Une erreur est survenue.'
      setStatus(s => ({ ...s, [action]: { type: 'error', text } }))
    } finally {
      setLoading(l => ({ ...l, [action]: false }))
    }
  }

  return (
    <div className={styles.page}>
      <PageHeader
        title="Pipeline de données"
        subtitle="Déclenchez la collecte des articles et les traitements du modèle."
      />

      <div className={styles.grid}>
        {/* Scraping card */}
        <div className={styles.card}>
          <div className={styles.cardIcon} style={{ background: 'var(--brand-soft)' }}>
            <Play size={24} color="var(--brand)" />
          </div>
          <h2 className={styles.cardTitle}>Collecte des articles</h2>
          <p className={styles.cardDesc}>
            Récupère les articles de la presse tunisienne et exécute tout le pipeline ETL :
            génération des embeddings et analyse de sentiment.
          </p>

          <div className={styles.field}>
            <label className={styles.label}>Nombre max de pages</label>
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
            {loading.scrape ? 'En cours…' : 'Lancer la collecte'}
          </button>
        </div>

        {/* Clustering card */}
        <div className={styles.card}>
          <div className={styles.cardIcon} style={{ background: 'color-mix(in srgb, var(--positive) 12%, transparent)' }}>
            <GitMerge size={24} color="var(--positive)" />
          </div>
          <h2 className={styles.cardTitle}>Regroupement thématique</h2>
          <p className={styles.cardDesc}>
            Exécute le clustering BERTopic sur tous les articles stockés pour découvrir
            et assigner les thèmes. Met à jour les libellés de thème.
          </p>

          <StatusMessage status={status.cluster} />

          <button
            className={`${styles.actionBtn} ${styles.clusterBtn}`}
            onClick={handleClusterClick}
            disabled={loading.cluster}
          >
            {loading.cluster ? 'En cours…' : 'Lancer le clustering'}
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
