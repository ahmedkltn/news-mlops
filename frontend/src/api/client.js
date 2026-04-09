import axios from 'axios'

// Relative base — requests go to whatever origin served the app.
// Dev:    Vite proxies /api → http://localhost:8000
// Docker: nginx proxies /api → http://api:8000
const client = axios.create({ baseURL: '/api' })

export default client
