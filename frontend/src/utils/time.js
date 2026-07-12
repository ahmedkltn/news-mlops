// French relative + absolute time helpers for article timestamps.

export function relativeTime(str) {
  if (!str) return ''
  const then = new Date(str)
  if (Number.isNaN(then.getTime())) return ''
  const secs = Math.round((Date.now() - then.getTime()) / 1000)

  if (secs < 60) return "à l'instant"
  const mins = Math.round(secs / 60)
  if (mins < 60) return `il y a ${mins} min`
  const hours = Math.round(mins / 60)
  if (hours < 24) return `il y a ${hours} h`
  const days = Math.round(hours / 24)
  if (days < 7) return `il y a ${days} j`
  return formatDate(str)
}

export function formatDate(str) {
  if (!str) return '—'
  const d = new Date(str)
  if (Number.isNaN(d.getTime())) return '—'
  return d.toLocaleDateString('fr-FR', {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}

export function todayLong() {
  return new Date().toLocaleDateString('fr-FR', {
    weekday: 'long', day: 'numeric', month: 'long', year: 'numeric',
  })
}
