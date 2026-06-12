import React, { useEffect, useRef, useState } from 'react'
import {
  Play,
  Monitor,
  Smartphone,
  Tablet,
  CheckCircle,
  Loader,
  XCircle,
} from 'lucide-react'

import { api, CrawlRun } from '../api/client'
import StatusBadge from '../components/StatusBadge'

const DEVICES = [
  { id: 'desktop', label: 'Desktop', icon: Monitor },
  { id: 'mobile', label: 'Mobile', icon: Smartphone },
  { id: 'tablet', label: 'Tablet', icon: Tablet },
]

export default function ManualCrawlPage() {
  const [keywords, setKeywords] = useState('')
  const [devices, setDevices] = useState<string[]>(['desktop'])
  const [profiles, setProfiles] = useState('Profile 44')

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [runId, setRunId] = useState<string | null>(null)
  const [runStatus, setRunStatus] = useState<CrawlRun | null>(null)

  const pollRef = useRef<NodeJS.Timeout | null>(null)

  function toggleDevice(id: string) {
    setDevices(prev =>
      prev.includes(id)
        ? prev.filter(d => d !== id)
        : [...prev, id]
    )
  }

  async function startCrawl() {
    const kws = keywords
      .split('\n')
      .map(k => k.trim())
      .filter(Boolean)

    if (!kws.length) {
      setError('Vui lòng nhập keyword')
      return
    }

    if (!devices.length) {
      setError('Vui lòng chọn device')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const res = await api.startCrawl({
        keywords: kws,
        devices,
        profiles: profiles
          .split(',')
          .map(p => p.trim())
          .filter(Boolean),
      })

      setRunId(res.run_id)
      startPolling(res.run_id)
    } catch (e: any) {
      setError(e.message || 'Không thể crawl')
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

        if (
          status.status === 'completed' ||
          status.status === 'failed'
        ) {
          clearInterval(pollRef.current!)
        }
      } catch (e) {
        console.error(e)
      }
    }, 3000)
  }

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

  const progress =
    runStatus && runStatus.total_keywords > 0
      ? Math.round(
          (runStatus.processed_keywords /
            runStatus.total_keywords) *
            100
        )
      : 0

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1
          className="text-3xl font-bold"
          style={{ color: 'var(--text-primary)' }}
        >
          Crawl Thủ Công
        </h1>

        <p
          className="text-sm mt-1"
          style={{ color: 'var(--text-muted)' }}
        >
          Crawl quảng cáo Google bằng tay
        </p>
      </div>

      <div
        className="rounded-2xl border p-6"
        style={{
          background: 'var(--bg-card)',
          borderColor: 'var(--border)',
        }}
      >
        <div className="mb-6">
          <label
            className="block text-xs font-semibold uppercase tracking-widest mb-3"
            style={{ color: 'var(--text-muted)' }}
          >
            Keywords
          </label>

          <textarea
            rows={8}
            value={keywords}
            onChange={e => setKeywords(e.target.value)}
            placeholder={`Nhập từ khóa tìm kiếm...`}
            className="w-full rounded-xl p-4 text-sm font-mono resize-y"
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border)',
              color: 'var(--text-primary)',
            }}
          />
        </div>

        <div className="mb-6">
          <label
            className="block text-xs font-semibold uppercase tracking-widest mb-3"
            style={{ color: 'var(--text-muted)' }}
          >
            Devices
          </label>

          <div className="flex gap-3">
            {DEVICES.map(({ id, label, icon: Icon }) => {
              const active = devices.includes(id)

              return (
                <button
                  key={id}
                  onClick={() => toggleDevice(id)}
                  className="flex-1 flex items-center justify-center gap-2 px-5 py-3 rounded-xl border transition-all"
                  style={{
                    background: active
                      ? 'var(--accent-dim)'
                      : 'var(--bg-secondary)',
                    borderColor: active
                      ? 'var(--accent)'
                      : 'var(--border)',
                    color: active
                      ? 'white'
                      : 'var(--text-secondary)',
                  }}
                >
                  <Icon size={18} />
                  {label}
                  {active && <CheckCircle size={16} />}
                </button>
              )
            })}
          </div>
        </div>

        <div className="mb-8">
          <label
            className="block text-xs font-semibold uppercase tracking-widest mb-3"
            style={{ color: 'var(--text-muted)' }}
          >
            Chrome Profiles
          </label>

          <input
            value={profiles}
            onChange={e => setProfiles(e.target.value)}
            placeholder="Profile 44"
            className="w-full rounded-xl px-4 py-3"
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border)',
            }}
          />
        </div>

        {error && (
          <div className="flex items-center gap-2 p-4 rounded-xl mb-4 text-red-400 bg-red-900/20 border border-red-800">
            <XCircle size={20} />
            {error}
          </div>
        )}

        <button
          onClick={startCrawl}
          disabled={loading}
          className="w-full py-4 text-lg font-bold rounded-2xl flex items-center justify-center gap-3 transition-all"
          style={{
            background: loading
              ? '#4b5563'
              : 'var(--accent)',
            color: 'white',
          }}
        >
          {loading ? (
            <Loader className="animate-spin" size={22} />
          ) : (
            <Play size={22} />
          )}

          {loading
            ? 'Đang khởi tạo...'
            : 'BẮT ĐẦU CRAWL'}
        </button>
      </div>

      {runId && runStatus && (
        <div
          className="mt-8 rounded-xl border p-5"
          style={{
            background: 'var(--bg-card)',
            borderColor: 'var(--border)',
          }}
        >
          <div className="flex items-center justify-between mb-4">
            <div>
              <StatusBadge status={runStatus.status} />

              <p
                className="text-xs mono mt-1"
                style={{ color: 'var(--text-muted)' }}
              >
                {runId}
              </p>
            </div>

            <p
              className="text-2xl font-bold mono"
              style={{ color: 'var(--text-primary)' }}
            >
              {progress}%
            </p>
          </div>

          <div
            className="h-2 rounded-full overflow-hidden mb-3"
            style={{ background: 'var(--bg-secondary)' }}
          >
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${progress}%`,
                background: 'var(--accent)',
              }}
            />
          </div>
        </div>
      )}
    </div>
  )
}