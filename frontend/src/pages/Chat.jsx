import { useState, useRef, useEffect } from 'react'
import { Send, Loader2, MessageCircle, ExternalLink, Bot, User } from 'lucide-react'
import client from '../api/client'
import styles from './Chat.module.css'

export default function Chat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function handleSubmit(e) {
    e.preventDefault()
    const q = input.trim()
    if (!q || loading) return

    setMessages(prev => [...prev, { role: 'user', text: q }])
    setInput('')
    setLoading(true)

    try {
      const res = await client.post('/genai/chat', { q })
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: res.data?.answer || 'No answer returned.',
        sources: res.data?.sources || [],
      }])
    } catch (err) {
      console.error(err)
      setMessages(prev => [...prev, {
        role: 'assistant',
        error: true,
        text: "Sorry, something went wrong answering that question. Please try again.",
      }])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.page}>
      <h1 className={styles.pageTitle}>Ask the news</h1>
      <p className={styles.subtitle}>Ask a question and get an answer grounded in recent articles</p>

      <div className={styles.chatBox}>
        <div className={styles.messages}>
          {messages.length === 0 && !loading && (
            <div className={styles.empty}>
              <MessageCircle size={28} className={styles.emptyIcon} />
              <p>Ask something like "What's happening in Tunisian politics this week?"</p>
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
                    <div className={styles.sourcesLabel}>Sources</div>
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
                  <Loader2 size={14} className={styles.spin} /> Thinking...
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
            placeholder="Ask a question about the news..."
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
