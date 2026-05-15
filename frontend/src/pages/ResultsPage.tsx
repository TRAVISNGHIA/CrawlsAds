import React, { useState, useEffect, useCallback } from 'react'
import { Search, X, RefreshCw, Trash2, Filter } from 'lucide-react'
import { api, AdResult } from '../api/client'
import ResultTable from '../components/ResultTable'

export default function ResultsPage() {
  const [results, setResults] = useState<AdResult[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [keyword, setKeyword] = useState('')
  const [device, setDevice] = useState('')
  const [domain, setDomain] = useState('')
  const [hasAds, setHasAds] = useState<string>('')

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api.getResults({
        keyword: keyword || undefined,
        device: device || undefined,
        domain: domain || undefined,
        has_ads: hasAds === '' ? undefined : hasAds === 'true',
        limit: 200,
      })
      setResults(res.results)
      setTotal(res.total)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }, [keyword, device, domain, hasAds])

  useEffect(() => { load() }, [load])

  async function clearAll() {
    if (!confirm('Delete all results?')) return
    await api.clearResults()
    await load()
  }

  function clearFilters() {
    setKeyword('')
    setDevice('')
    setDomain('')
    setHasAds('')
  }

  const hasFilters = keyword || device || domain || hasAds

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6 fade-in">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>Results</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
            Showing {results.length} of {total} total results
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={load} className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors"
            style={{ background: 'var(--bg-card)', color: 'var(--text-secondary)', border: '1px solid var(--border)' }}>
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
          <button onClick={clearAll} className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors"
            style={{ background: 'rgba(239,68,68,0.1)', color: '#f87171', border: '1px solid rgba(239,68,68,0.2)' }}>
            <Trash2 size={14} />
            Clear All
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="rounded-xl border p-4 mb-6 fade-in-1" style={{ background: 'var(--bg-card)', borderColor: 'var(--border)' }}>
        <div className="flex items-center gap-2 mb-3">
          <Filter size={14} style={{ color: 'var(--text-muted)' }} />
          <span className="text-xs font-semibold uppercase tracking-widest" style={{ color: 'var(--text-muted)' }}>Filters</span>
          {hasFilters && (
            <button onClick={clearFilters} className="ml-auto flex items-center gap-1 text-xs px-2 py-1 rounded transition-colors"
              style={{ color: 'var(--text-muted)', background: 'var(--bg-secondary)' }}>
              <X size={10} /> Clear
            </button>
          )}
        </div>
        <div className="grid grid-cols-4 gap-3">
          {[
            { value: keyword, set: setKeyword, placeholder: 'Filter by keyword…', icon: <Search size={12} /> },
            { value: domain, set: setDomain, placeholder: 'Filter by domain…', icon: null },
          ].map((f, i) => (
            <div key={i} className="relative">
              {f.icon && <span className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--text-muted)' }}>{f.icon}</span>}
              <input
                className="w-full rounded-lg py-2 text-xs mono outline-none transition-all"
                style={{
                  background: 'var(--bg-secondary)',
                  border: '1px solid var(--border)',
                  color: 'var(--text-primary)',
                  paddingLeft: f.icon ? '28px' : '12px',
                  paddingRight: '12px',
                }}
                placeholder={f.placeholder}
                value={f.value}
                onChange={e => f.set(e.target.value)}
              />
            </div>
          ))}

          <select
            value={device}
            onChange={e => setDevice(e.target.value)}
            className="rounded-lg px-3 py-2 text-xs mono outline-none transition-all appearance-none cursor-pointer"
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border)',
              color: device ? 'var(--text-primary)' : 'var(--text-muted)',
            }}>
            <option value="">All devices</option>
            <option value="desktop">Desktop</option>
            <option value="mobile">Mobile</option>
            <option value="tablet">Tablet</option>
          </select>

          <select
            value={hasAds}
            onChange={e => setHasAds(e.target.value)}
            className="rounded-lg px-3 py-2 text-xs mono outline-none transition-all appearance-none cursor-pointer"
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border)',
              color: hasAds ? 'var(--text-primary)' : 'var(--text-muted)',
            }}>
            <option value="">All results</option>
            <option value="true">Has ads</option>
            <option value="false">No ads</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="fade-in-2">
        {loading ? (
          <div className="text-center py-16" style={{ color: 'var(--text-muted)' }}>
            <RefreshCw size={24} className="animate-spin mx-auto mb-3" />
            <p className="text-sm">Loading results…</p>
          </div>
        ) : (
          <ResultTable results={results} />
        )}
      </div>
    </div>
  )
}
