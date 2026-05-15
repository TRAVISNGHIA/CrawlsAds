import React, { useEffect, useState } from 'react'
import { BarChart3, Search, TrendingUp, Activity, RefreshCw } from 'lucide-react'
import { api, Stats, CrawlRun } from '../api/client'
import StatusBadge from '../components/StatusBadge'

function StatCard({ label, value, icon: Icon, accent = false }: { label: string; value: string | number; icon: any; accent?: boolean }) {
  return (
    <div className="rounded-xl p-5 border transition-all duration-200 fade-in"
      style={{
        background: accent ? 'var(--accent-dim)' : 'var(--bg-card)',
        borderColor: accent ? 'var(--accent)' : 'var(--border)',
      }}>
      <div className="flex items-center justify-between mb-3">
        <p className="text-xs font-semibold uppercase tracking-widest" style={{ color: accent ? '#c4b5fd' : 'var(--text-muted)' }}>{label}</p>
        <Icon size={16} style={{ color: accent ? '#c4b5fd' : 'var(--text-muted)' }} />
      </div>
      <p className="text-3xl font-bold mono" style={{ color: accent ? 'white' : 'var(--text-primary)' }}>
        {typeof value === 'number' ? value.toLocaleString() : value}
      </p>
    </div>
  )
}

function RunRow({ run }: { run: CrawlRun }) {
  const progress = run.total_keywords > 0
    ? Math.round((run.processed_keywords / run.total_keywords) * 100)
    : 0

  return (
    <div className="flex items-center gap-4 p-4 rounded-lg border transition-colors"
      style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)' }}>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <StatusBadge status={run.status} />
          <span className="text-xs mono truncate" style={{ color: 'var(--text-muted)' }}>{run.run_id}</span>
        </div>
        <p className="text-xs" style={{ color: 'var(--text-secondary)' }}>
          {run.processed_keywords}/{run.total_keywords} keywords · {Array.isArray(run.devices) && run.devices.length > 0 ? run.devices.join(", ") : "—"}
        </p>
        {run.status === 'running' && (
          <div className="mt-2 h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--bg-primary)' }}>
            <div className="h-full rounded-full progress-shimmer transition-all" style={{ width: `${progress}%` }} />
          </div>
        )}
      </div>
      <div className="text-right">
        <p className="text-xs mono" style={{ color: 'var(--text-muted)' }}>
          {run.started_at ? new Date(run.started_at).toLocaleString() : '—'}
        </p>
      </div>
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [runs, setRuns] = useState<CrawlRun[]>([])
  const [loading, setLoading] = useState(true)

  async function load() {
    try {
      const [s, r] = await Promise.all([api.getStats(), api.listRuns()])
      setStats(s)
      setRuns(r.runs)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [])

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8 fade-in">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>Dashboard</h1>
          <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>Google SEM ad monitoring overview</p>
        </div>
        <button onClick={load} className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          style={{ background: 'var(--bg-card)', color: 'var(--text-secondary)', border: '1px solid var(--border)' }}>
          <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard label="Total Runs" value={stats?.total_runs ?? 0} icon={Activity} />
        <StatCard label="Keywords Checked" value={stats?.total_unique_keywords ?? 0} icon={Search} />
        <StatCard label="Ads Found" value={stats?.total_ads_found ?? 0} icon={TrendingUp} accent />
        <StatCard label="Total Results" value={stats?.total_results ?? 0} icon={BarChart3} />
      </div>

      {/* Recent runs */}
      <div className="fade-in-2">
        <h2 className="text-sm font-semibold uppercase tracking-widest mb-4" style={{ color: 'var(--text-muted)' }}>
          Recent Crawl Runs
        </h2>
        {runs.length === 0 ? (
          <div className="rounded-xl border p-12 text-center" style={{ borderColor: 'var(--border)', background: 'var(--bg-card)' }}>
            <p className="text-4xl mb-3">🚀</p>
            <p className="text-sm" style={{ color: 'var(--text-muted)' }}>No crawl runs yet. Start one from the Crawl page.</p>
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {runs.map(run => <RunRow key={run.run_id} run={run} />)}
          </div>
        )}
      </div>
    </div>
  )
}
