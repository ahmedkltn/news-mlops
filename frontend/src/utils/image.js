// Route remote article images through our same-origin proxy so hotlink /
// cross-site WAF protection (e.g. lapresse.tn) can't swap in a placeholder.
export function proxied(url) {
  if (!url || typeof url !== 'string') return url
  if (!/^https?:\/\//i.test(url)) return url
  return `/api/img?url=${encodeURIComponent(url)}`
}
