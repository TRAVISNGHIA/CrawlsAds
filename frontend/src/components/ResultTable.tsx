import React, { useState } from 'react'
import { ExternalLink, Image, ChevronDown, ChevronUp, Monitor, Smartphone, Tablet } from 'lucide-react'
import type { AdResult } from '../api/client'

interface Props {
  results: AdResult[]
}

const DEVICE_ICON: Record<string, React.ReactNode> = {
  desktop: <Monitor size={12} />,
  mobile: <Smartphone size={12} />,
  tablet: <Tablet size={12} />,
}

function truncate(str: string | undefined, n = 40) {
  if (!str) return '—'
  return str.length > n ? str.slice(0, n) + '…' : str
}

interface RowDetailProps {
  result: AdResult
  onClose: () => void
}

function ResultModal({ result, onClose }: RowDetailProps) {
  const screenshotUrl = result.screenshot_path ? `/${result.screenshot_path}` : null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4" onClick={onClose}
      style={{ background: 'rgba(0,0,0,0.8)' }}>
      <div className="rounded-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto p-6 fade-in"
        style={{ background: 'var(--bg-card)', border: '1px solid var(--border-bright)' }}
        onClick={e => e.stopPropagation()}>
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="text-lg font-bold" style={{ color: 'var(--text-primary)' }}>
              {result.ad_title || 'No Title'}
            </h3>
            <p className="text-sm mono mt-1" style={{ color: 'var(--text-muted)' }}>
              {result.keyword} · {result.device} · {result.profile_name}
            </p>
          </div>
          <button onClick={onClose} className="text-sm px-3 py-1 rounded-lg transition-colors"
            style={{ color: 'var(--text-secondary)', background: 'var(--bg-secondary)' }}>
            Close
          </button>
        </div>

        <div className="grid grid-cols-2 gap-3 text-sm mb-4">
          {[
            ['Advertiser', result.advertiser],
            ['Visible Domain', result.visible_domain],
            ['Final Domain', result.final_domain],
            ['Position', result.ad_position],
            ['Has Ads', result.has_ads ? 'Yes' : 'No'],
            ['Created', new Date(result.created_at).toLocaleString()],
          ].map(([label, value]) => (
            <div key={label as string} className="rounded-lg p-3" style={{ background: 'var(--bg-secondary)' }}>
              <p className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>{label}</p>
              <p className="font-medium mono break-all" style={{ color: 'var(--text-primary)' }}>
                {value != null && value !== '' ? String(value) : '—'}
              </p>
            </div>
          ))}
        </div>

        {result.raw_url && (
          <div className="rounded-lg p-3 mb-3" style={{ background: 'var(--bg-secondary)' }}>
            <p className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>Raw URL</p>
            <p className="text-xs mono break-all" style={{ color: 'var(--cyan)' }}>{result.raw_url}</p>
          </div>
        )}

        {result.final_url && (
          <div className="rounded-lg p-3 mb-4" style={{ background: 'var(--bg-secondary)' }}>
            <p className="text-xs mb-1" style={{ color: 'var(--text-muted)' }}>Final URL</p>
            <a href={result.final_url} target="_blank" rel="noopener noreferrer"
              className="text-xs mono break-all hover:underline" style={{ color: 'var(--accent)' }}>
              {result.final_url}
            </a>
          </div>
        )}

        {screenshotUrl && (
          <div>
            <p className="text-xs mb-2" style={{ color: 'var(--text-muted)' }}>Screenshot</p>
            <img src={screenshotUrl} alt="Screenshot" className="w-full rounded-lg border"
              style={{ borderColor: 'var(--border)' }} />
          </div>
        )}
      </div>
    </div>
  )
}

export default function ResultTable({ results }: Props) {
  const [selected, setSelected] = useState<AdResult | null>(null)
  const [sortField, setSortField] = useState<keyof AdResult>('created_at')
  const [sortAsc, setSortAsc] = useState(false)

  const sorted = [...results].sort((a, b) => {
    const av = a[sortField] ?? ''
    const bv = b[sortField] ?? ''
    const cmp = String(av).localeCompare(String(bv))
    return sortAsc ? cmp : -cmp
  })

  function toggleSort(field: keyof AdResult) {
    if (sortField === field) setSortAsc(!sortAsc)
    else { setSortField(field); setSortAsc(true) }
  }

  function SortIcon({ field }: { field: keyof AdResult }) {
    if (sortField !== field) return null
    return sortAsc ? <ChevronUp size={12} /> : <ChevronDown size={12} />
  }

  const cols: { label: string; field: keyof AdResult }[] = [
    { label: 'Keyword', field: 'keyword' },
    { label: 'Device', field: 'device' },
    { label: 'Profile', field: 'profile_name' },
    { label: 'Ad Title', field: 'ad_title' },
    { label: 'Advertiser', field: 'advertiser' },
    { label: 'Domain', field: 'final_domain' },
    { label: 'Date', field: 'created_at' },
  ]

  if (results.length === 0) {
    return (
      <div className="text-center py-16" style={{ color: 'var(--text-muted)' }}>
        <p className="text-4xl mb-3">🔍</p>
        <p className="text-sm">No results found</p>
      </div>
    )
  }

  return (
    <>
      <div className="overflow-x-auto rounded-xl border" style={{ borderColor: 'var(--border)' }}>
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr style={{ background: 'var(--bg-secondary)', borderBottom: '1px solid var(--border)' }}>
              {cols.map(col => (
                <th key={col.field}
                  className="px-4 py-3 text-left text-xs font-semibold cursor-pointer hover:text-white transition-colors select-none"
                  style={{ color: 'var(--text-muted)' }}
                  onClick={() => toggleSort(col.field)}>
                  <span className="flex items-center gap-1">
                    {col.label} <SortIcon field={col.field} />
                  </span>
                </th>
              ))}
              <th className="px-4 py-3 text-left text-xs font-semibold" style={{ color: 'var(--text-muted)' }}>
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {sorted.map((r, i) => (
              <tr key={r._id}
                className="border-b cursor-pointer transition-colors"
                style={{
                  borderColor: 'var(--border)',
                  background: i % 2 === 0 ? 'var(--bg-card)' : 'var(--bg-secondary)',
                }}
                onMouseEnter={e => (e.currentTarget.style.background = 'var(--bg-card-hover)')}
                onMouseLeave={e => (e.currentTarget.style.background = i % 2 === 0 ? 'var(--bg-card)' : 'var(--bg-secondary)')}
                onClick={() => setSelected(r)}>
                <td className="px-4 py-3 font-medium" style={{ color: 'var(--text-primary)' }}>
                  <span className="mono text-xs">{r.keyword}</span>
                </td>
                <td className="px-4 py-3">
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs"
                    style={{ background: 'var(--bg-secondary)', color: 'var(--text-secondary)', border: '1px solid var(--border)' }}>
                    {DEVICE_ICON[r.device]} {r.device}
                  </span>
                </td>
                <td className="px-4 py-3 text-xs mono" style={{ color: 'var(--text-secondary)' }}>{r.profile_name}</td>
                <td className="px-4 py-3 text-xs" style={{ color: r.has_ads ? 'var(--text-primary)' : 'var(--text-muted)' }}>
                  {truncate(r.ad_title, 45)}
                </td>
                <td className="px-4 py-3 text-xs" style={{ color: 'var(--text-secondary)' }}>
                  {truncate(r.advertiser, 30)}
                </td>
                <td className="px-4 py-3">
                  {r.final_domain ? (
                    <span className="text-xs mono px-2 py-0.5 rounded" style={{ background: 'var(--accent-dim)', color: 'var(--accent)' }}>
                      {r.final_domain}
                    </span>
                  ) : <span style={{ color: 'var(--text-muted)' }}>—</span>}
                </td>
                <td className="px-4 py-3 text-xs mono" style={{ color: 'var(--text-muted)' }}>
                  {new Date(r.created_at).toLocaleDateString()}
                </td>
                <td className="px-4 py-3" onClick={e => e.stopPropagation()}>
                  <div className="flex items-center gap-2">
                    {r.screenshot_path && (
                      <a href={`/${r.screenshot_path}`} target="_blank" rel="noopener noreferrer"
                        title="View screenshot"
                        className="p-1 rounded transition-colors hover:text-white"
                        style={{ color: 'var(--text-muted)' }}>
                        <Image size={14} />
                      </a>
                    )}
                    {r.final_url && (
                      <a href={r.final_url} target="_blank" rel="noopener noreferrer"
                        title="Open final URL"
                        className="p-1 rounded transition-colors hover:text-white"
                        style={{ color: 'var(--text-muted)' }}>
                        <ExternalLink size={14} />
                      </a>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {selected && <ResultModal result={selected} onClose={() => setSelected(null)} />}
    </>
  )
}
