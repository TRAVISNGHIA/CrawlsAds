import { Routes, Route } from 'react-router-dom'

import Navbar from './components/Navbar'

import Dashboard from './pages/Dashboard'
import ResultsPage from './pages/ResultsPage'

import ManualCrawlPage from './pages/ManualCrawlPage'
import AutoCrawlPage from './pages/AutoCrawlPage'
import KeywordsPage from './pages/KeywordsPage'

export default function App() {
  return (
    <div className="flex h-screen">
      <div className="w-[260px] shrink-0">
        <Navbar />
      </div>

      <div className="flex-1 overflow-auto">
        <Routes>
          <Route path="/" element={<Dashboard />} />

          <Route
            path="/manual-crawl"
            element={<ManualCrawlPage />}
          />

          <Route
            path="/auto-crawl"
            element={<AutoCrawlPage />}
          />

          <Route
            path="/keywords"
            element={<KeywordsPage />}
          />

          <Route
            path="/results"
            element={<ResultsPage />}
          />
        </Routes>
      </div>
    </div>
  )
}