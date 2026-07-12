import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, MessageCircle, ExternalLink, Bot, User } from 'lucide-react'
import client from '../api/client'
import PageHeader from '../components/PageHeader'
import styles from './Chat.module.css'

const SUGGESTIONS = [
  'Que se passe-t-il en Tunisie cette semaine ?',
  "Résume l'actualité économique récente",
  'Quelles sont les dernières nouvelles sportives ?',
]

export default function Chat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

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
        role: 'assistant',
        error: true,
        text: "Désolé, une erreur est survenue. Veuillez réessayer.",
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
    <div className={styles.page}>
      <PageHeader
        title="Assistant IA"
        subtitle="Posez une question et obtenez une réponse fondée sur les articles récents, avec ses sources."
      />

      <div className={styles.chatBox}>
        <div className={styles.messages}>
          {messages.length === 0 && !loading && (
            <div className={styles.empty}>
              <MessageCircle size={28} className={styles.emptyIcon} />
              <p>Essayez une question comme&nbsp;:</p>
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
            <div
              key={i}
              className={`${styles.message} ${m.role === 'user' ? styles.messageUser : styles.messageAssistant}`}
            >
              <div className={styles.messageIcon}>
                {m.role === 'user' ? <User size={16} /> : <Bot size={16} />}
              </div>
              <div className={styles.messageBody}>
                <div className={`${styles.messageText} ${m.error ? styles.messageError : ''}`}>
                  {m.text}
                </div>
                {m.sources && m.sources.length > 0 && (
                  <div className={styles.sources}>
                    <div className={styles.sourcesLabel}>Sources citées</div>
                    <ul className={styles.sourcesList}>
                      {m.sources.map((source) => (
                        <li key={source.id}>
                          <a
                            href={source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={styles.sourceLink}
                          >
                            <ExternalLink size={12} />
                            {source.title}
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
            <div className={`${styles.message} ${styles.messageAssistant}`}>
              <div className={styles.messageIcon}><Bot size={16} /></div>
              <div className={styles.messageBody}>
                <div className={styles.loadingText}>
                  <Loader2 size={14} className={styles.spin} /> Réflexion…
                </div>
              </div>
            </div>
          )}

          <div ref={endRef} />
        </div>

        <form className={styles.inputForm} onSubmit={handleSubmit}>
          <input
            className={styles.input}
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Posez une question sur l'actualité…"
            disabled={loading}
            autoFocus
          />
          <button type="submit" className={styles.sendBtn} disabled={loading || !input.trim()}>
            {loading ? <Loader2 size={16} className={styles.spin} /> : <Send size={16} />}
          </button>
        </form>
      </div>
    </div>
  )
}
