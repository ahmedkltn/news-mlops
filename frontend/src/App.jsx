import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Masthead from './components/Masthead'
import ChatWidget from './components/ChatWidget'
import Reader from './pages/Reader'
import Dashboard from './pages/Dashboard'
import Articles from './pages/Articles'
import Search from './pages/Search'
import Pipeline from './pages/Pipeline'
import Carte from './pages/Carte'
import styles from './App.module.css'

export default function App() {
  return (
    <BrowserRouter>
      <Masthead />
      <main className={styles.main}>
        <Routes>
          <Route path="/" element={<Reader />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/articles" element={<Articles />} />
          <Route path="/search" element={<Search />} />
          <Route path="/carte" element={<Carte />} />
          <Route path="/pipeline" element={<Pipeline />} />
        </Routes>
      </main>
      <ChatWidget />
    </BrowserRouter>
  )
}
