import { AlertTriangle } from 'lucide-react'
import styles from './ConfirmDialog.module.css'

export default function ConfirmDialog({ title, message, onConfirm, onCancel }) {
  return (
    <div className={styles.overlay} onClick={onCancel}>
      <div className={styles.dialog} onClick={(e) => e.stopPropagation()}>
        <div className={styles.icon}>
          <AlertTriangle size={22} color="var(--accent)" />
        </div>
        <h3 className={styles.title}>{title}</h3>
        <p className={styles.message}>{message}</p>
        <div className={styles.actions}>
          <button className={styles.cancelBtn} onClick={onCancel}>Annuler</button>
          <button className={styles.confirmBtn} onClick={onConfirm}>Confirmer</button>
        </div>
      </div>
    </div>
  )
}
