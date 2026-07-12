import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, Sparkles, ExternalLink, Bot, User, X } from 'lucide-react'
import client from '../api/client'
import styles from './ChatWidget.module.css'

const SUGGESTIONS = [
  'Que se passe-t-il en Tunisie cette semaine ?',
  "Résume l'actualité économique récente",
  'Dernières nouvelles sportives ?',
]

export default function ChatWidget() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const endRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => {
    if (open) inputRef.current?.focus()
    const onKey = e => { if (e.key === 'Escape') setOpen(false) }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open])

  async function ask(text) {
    const q = (text || '').trim()
    if (!q || loading) return
    setMessages(prev => [...prev, { role: 'user', text: q }])
    setInput('')
    setLoading(true)
    try {
      const res = await client.post('/genai/chat', { q })
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: res.data?.answer || 'Aucune réponse renvoyée.',
        sources: res.data?.sources || [],
      }])
    } catch (err) {
      console.error(err)
      setMessages(prev => [...prev, {
        role: 'assistant', error: true,
        text: 'Désolé, une erreur est survenue. Veuillez réessayer.',
      }])
    } finally {
      setLoading(false)
    }
  }

  function handleSubmit(e) {
    e.preventDefault()
    ask(input)
  }

  return (
    <>
      {open && (
        <div className={styles.panel} role="dialog" aria-label="Assistant IA">
          <div className={styles.head}>
            <div className={styles.headTitle}>
              <Sparkles size={16} className={styles.headIcon} />
              Assistant IA
            </div>
            <button className={styles.headClose} onClick={() => setOpen(false)} aria-label="Fermer l'assistant">
              <X size={18} />
            </button>
          </div>

          <div className={styles.messages}>
            {messages.length === 0 && !loading && (
              <div className={styles.empty}>
                <Bot size={26} className={styles.emptyIcon} />
                <p>Posez une question sur l'actualité tunisienne. Les réponses citent leurs sources.</p>
                <div className={styles.suggestions}>
                  {SUGGESTIONS.map(s => (
                    <button key={s} type="button" className={styles.suggestion} onClick={() => ask(s)}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((m, i) => (
              <div key={i} className={`${styles.message} ${m.role === 'user' ? styles.user : styles.assistant}`}>
                <div className={styles.msgIcon}>
                  {m.role === 'user' ? <User size={15} /> : <Bot size={15} />}
                </div>
                <div className={styles.msgBody}>
                  <div className={`${styles.msgText} ${m.error ? styles.msgError : ''}`}>{m.text}</div>
                  {m.sources && m.sources.length > 0 && (
                    <div className={styles.sources}>
                      <div className={styles.sourcesLabel}>Sources</div>
                      <ul>
                        {m.sources.map(s => (
                          <li key={s.id}>
                            <a href={s.url} target="_blank" rel="noopener noreferrer" className={styles.sourceLink}>
                              <ExternalLink size={11} />{s.title}
                            </a>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className={`${styles.message} ${styles.assistant}`}>
                <div className={styles.msgIcon}><Bot size={15} /></div>
                <div className={styles.msgBody}>
                  <div className={styles.loadingText}><Loader2 size={13} className={styles.spin} /> Réflexion…</div>
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>

          <form className={styles.inputForm} onSubmit={handleSubmit}>
            <input
              ref={inputRef}
              className={styles.input}
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Posez une question…"
              disabled={loading}
            />
            <button type="submit" className={styles.sendBtn} disabled={loading || !input.trim()} aria-label="Envoyer">
              {loading ? <Loader2 size={16} className={styles.spin} /> : <Send size={16} />}
            </button>
          </form>
        </div>
      )}

      <button
        className={`${styles.fab} ${open ? styles.fabOpen : ''}`}
        onClick={() => setOpen(o => !o)}
        aria-label={open ? "Fermer l'assistant" : "Ouvrir l'assistant IA"}
        aria-expanded={open}
      >
        {open ? <X size={22} /> : <Sparkles size={22} />}
      </button>
    </>
  )
}
