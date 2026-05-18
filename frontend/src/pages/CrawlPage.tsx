import React, { useState, useRef, useEffect } from 'react'
import { Play, Monitor, Smartphone, Tablet, Eye, EyeOff, CheckCircle, XCircle, Loader } from 'lucide-react'
import { api, CrawlRun } from '../api/client'
import StatusBadge from '../components/StatusBadge'

const DEVICES = [
  { id: 'desktop', label: 'Desktop', icon: Monitor },
  { id: 'mobile', label: 'Mobile', icon: Smartphone },
  { id: 'tablet', label: 'Tablet', icon: Tablet },
]

export default function CrawlPage() {
  const [keywords, setKeywords] = useState('')
  const [devices, setDevices] = useState<string[]>(['desktop'])
  const [profiles, setProfiles] = useState('Default')
  const [headless, setHeadless] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [runId, setRunId] = useState<string | null>(null)
  const [runStatus, setRunStatus] = useState<CrawlRun | null>(null)
  const pollRef = useRef<NodeJS.Timeout | null>(null)

  function toggleDevice(id: string) {
    setDevices(prev =>
      prev.includes(id) ? prev.filter(d => d !== id) : [...prev, id]
    )
  }

  async function startCrawl() {
    const kws = keywords.split('\n').map(k => k.trim()).filter(Boolean)
    if (!kws.length) { setError('Enter at least one keyword'); return }
    if (!devices.length) { setError('Select at least one device'); return }

    setLoading(true)
    setError(null)
    setRunStatus(null)

    try {
      const res = await api.startCrawl({
        keywords: kws,
        devices,
        profiles: profiles.split(',').map(p => p.trim()).filter(Boolean),

      })
      setRunId(res.run_id)
      startPolling(res.run_id)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  function startPolling(id: string) {
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = setInterval(async () => {
      try {
        const status = await api.getCrawlStatus(id)
        setRunStatus(status)
        if (['completed', 'failed'].includes(status.status)) {
          clearInterval(pollRef.current!)
        }
      } catch (e) {
        console.error('Poll error:', e)
      }
    }, 2500)
  }

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current) }, [])

  const progress = runStatus && runStatus.total_keywords > 0
    ? Math.round((runStatus.processed_keywords / runStatus.total_keywords) * 100)
    : 0

  return (
    <div className="p-8 max-w-3xl">
      <div className="mb-8 fade-in">
        <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>New Crawl</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>Configure and start a Google SEM ad check</p>
      </div>

      {/* Keywords */}
      <div className="rounded-xl border p-5 mb-4 fade-in-1" style={{ background: 'var(--bg-card)', borderColor: 'var(--border)' }}>
        <label className="block text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted)' }}>
          Keywords <span style={{ color: 'var(--text-secondary)' }}>— one per line</span>
        </label>
        <textarea
          className="w-full rounded-lg p-3 text-sm mono resize-y outline-none focus:ring-2 transition-all"
          rows={6}
          placeholder={"buy laptop\nonline loan\nreservation hotel hanoi"}
          value={keywords}
          onChange={e => setKeywords(e.target.value)}
          style={{
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border)',
            color: 'var(--text-primary)',
            '--tw-ring-color': 'var(--accent)',
          } as any}
        />
        <p className="text-xs mt-2 mono" style={{ color: 'var(--text-muted)' }}>
          {keywords.split('\n').filter(k => k.trim()).length} keyword(s)
        </p>
      </div>

      {/* Devices */}
      <div className="rounded-xl border p-5 mb-4 fade-in-2" style={{ background: 'var(--bg-card)', borderColor: 'var(--border)' }}>
        <label className="block text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted)' }}>
          Devices
        </label>
        <div className="flex gap-3">
          {DEVICES.map(({ id, label, icon: Icon }) => {
            const active = devices.includes(id)
            return (
              <button key={id} onClick={() => toggleDevice(id)}
                className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all border"
                style={{
                  background: active ? 'var(--accent-dim)' : 'var(--bg-secondary)',
                  borderColor: active ? 'var(--accent)' : 'var(--border)',
                  color: active ? 'white' : 'var(--text-secondary)',
                }}>
                <Icon size={14} />
                {label}
                {active && <CheckCircle size={12} style={{ color: 'var(--accent)' }} />}
              </button>
            )
          })}
        </div>
      </div>

      {/* Profile + Headless */}
      <div className="grid grid-cols-2 gap-4 mb-6 fade-in-3">
        <div className="rounded-xl border p-5" style={{ background: 'var(--bg-card)', borderColor: 'var(--border)' }}>
          <label className="block text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted)' }}>
            Chrome Profiles <span style={{ color: 'var(--text-secondary)' }}>— comma-separated</span>
          </label>
          <input
            className="w-full rounded-lg px-3 py-2.5 text-sm mono outline-none focus:ring-2 transition-all"
            placeholder="Default"
            value={profiles}
            onChange={e => setProfiles(e.target.value)}
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border)',
              color: 'var(--text-primary)',
            }}
          />
        </div>

        <div className="rounded-xl border p-5" style={{ background: 'var(--bg-card)', borderColor: 'var(--border)' }}>
          <label className="block text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: 'var(--text-muted)' }}>
            Headless Mode
          </label>
          <button onClick={() => setHeadless(!headless)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all border"
            style={{
              background: headless ? 'var(--accent-dim)' : 'var(--bg-secondary)',
              borderColor: headless ? 'var(--accent)' : 'var(--border)',
              color: headless ? 'white' : 'var(--text-secondary)',
            }}>
            {headless ? <EyeOff size={14} /> : <Eye size={14} />}
            {headless ? 'Headless ON' : 'Headless OFF'}
          </button>
          <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
            {headless ? 'Browser runs in background' : 'Browser window is visible'}
          </p>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 p-3 rounded-lg mb-4 text-sm"
          style={{ background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', color: '#f87171' }}>
          <XCircle size={15} /> {error}
        </div>
      )}

      {/* Start button */}
      <button onClick={startCrawl} disabled={loading}
        className="flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-bold transition-all glow-accent fade-in-4"
        style={{
          background: loading ? 'var(--accent-dim)' : 'var(--accent)',
          color: 'white',
          opacity: loading ? 0.7 : 1,
        }}>
        {loading ? <Loader size={16} className="animate-spin" /> : <Play size={16} />}
        {loading ? 'Starting…' : 'Start Crawl'}
      </button>

      {/* Live status */}
      {runId && runStatus && (
        <div className="mt-8 rounded-xl border p-5 fade-in" style={{ background: 'var(--bg-card)', borderColor: 'var(--border)' }}>
          <div className="flex items-center justify-between mb-4">
            <div>
              <StatusBadge status={runStatus.status} />
              <p className="text-xs mono mt-1" style={{ color: 'var(--text-muted)' }}>{runId}</p>
            </div>
            <p className="text-2xl font-bold mono" style={{ color: 'var(--text-primary)' }}>{progress}%</p>
          </div>

          {/* Progress bar */}
          <div className="h-2 rounded-full overflow-hidden mb-3" style={{ background: 'var(--bg-secondary)' }}>
            <div className={`h-full rounded-full transition-all duration-500 ${runStatus.status === 'running' ? 'progress-shimmer' : ''}`}
              style={{
                width: `${progress}%`,
                background: runStatus.status === 'completed' ? 'var(--green)'
                  : runStatus.status === 'failed' ? 'var(--red)'
                  : undefined,
              }} />
          </div>

          <div className="flex gap-6 text-xs" style={{ color: 'var(--text-secondary)' }}>
            <span className="mono">{runStatus.processed_keywords}/{runStatus.total_keywords} processed</span>
            <span>{runStatus.devices.join(', ')}</span>
            {runStatus.error && (
              <span style={{ color: 'var(--red)' }}>Error: {runStatus.error}</span>
            )}
          </div>

          {runStatus.status === 'completed' && (
            <p className="text-sm mt-3 font-medium" style={{ color: 'var(--green)' }}>
              ✓ Crawl complete! View results in the Results tab.
            </p>
          )}
        </div>
      )}
    </div>
  )
}
