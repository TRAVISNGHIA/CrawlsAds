const BASE_URL = '/api'

export interface CrawlStartPayload {
  keywords: string[]
  devices: string[]
  profiles: string[]
  headless: boolean
}

export interface CrawlRun {
  run_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  total_keywords: number
  processed_keywords: number
  devices: string[]
  profiles: string[]
  started_at: string
  finished_at?: string
  error?: string
  progress?: number
}

export interface AdResult {
  _id: string
  run_id: string
  keyword: string
  device: string
  profile_name: string
  has_ads: boolean
  ad_position: number
  ad_title?: string
  advertiser?: string
  visible_domain?: string
  raw_url?: string
  final_url?: string
  final_domain?: string
  screenshot_path?: string
  html_path?: string
  created_at: string
}

export interface Stats {
  total_runs: number
  total_results: number
  total_ads_found: number
  total_unique_keywords: number
  latest_run?: CrawlRun
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `Request failed: ${res.status}`)
  }
  return res.json()
}

export const api = {
  health: () => request<{ status: string }>('/health'),

  startCrawl: (payload: CrawlStartPayload) =>
    request<{ run_id: string; message: string }>('/crawl/start', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  getCrawlStatus: (runId: string) =>
    request<CrawlRun>(`/crawl/status/${runId}`),

  listRuns: () => request<{ runs: CrawlRun[]; count: number }>('/crawl/runs'),

  getResults: (params?: {
    keyword?: string
    device?: string
    domain?: string
    run_id?: string
    has_ads?: boolean
    limit?: number
    skip?: number
  }) => {
    const q = new URLSearchParams()
    if (params?.keyword) q.set('keyword', params.keyword)
    if (params?.device) q.set('device', params.device)
    if (params?.domain) q.set('domain', params.domain)
    if (params?.run_id) q.set('run_id', params.run_id)
    if (params?.has_ads !== undefined) q.set('has_ads', String(params.has_ads))
    if (params?.limit) q.set('limit', String(params.limit))
    if (params?.skip) q.set('skip', String(params.skip))
    const qs = q.toString()
    return request<{ results: AdResult[]; total: number }>(`/results${qs ? '?' + qs : ''}`)
  },

  getResult: (id: string) => request<AdResult>(`/results/${id}`),

  clearResults: (runId?: string) => {
    const q = runId ? `?run_id=${runId}` : ''
    return request<{ deleted: number }>(`/results${q}`, { method: 'DELETE' })
  },

  getStats: () => request<Stats>('/stats'),
}
