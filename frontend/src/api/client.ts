const BASE_URL = '/api'

export interface CrawlStartPayload {
  keywords: string[]
  devices: string[]
  profiles: string[]
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

export interface KeywordDoc {
  _id: string
  keyword: string
  created_at?: string
  last_crawled_at?: string | null
  crawl_count?: number
}

export interface KeywordPage {
  items: KeywordDoc[]
  total: number
  page: number
  limit: number
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

  getSchedulerConfig: async (): Promise<any> => {
    const res = await fetch('/api/crawl/auto/config', {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    })
    if (!res.ok) throw new Error('Không thể lấy cấu hình scheduler')
    return res.json()
  },

  updateSchedulerConfig: async (config: any): Promise<any> => {
    const res = await fetch('/api/crawl/auto/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    })
    if (!res.ok) {
      const error = await res.json().catch(() => ({}))
      throw new Error(error.message || 'Không thể cập nhật scheduler config')
    }
    return res.json()
  },
  getKeywords: (params: {
    page?: number
    limit?: number
    search?: string
  }): Promise<KeywordPage> => {
    const q = new URLSearchParams()
    if (params.page)   q.set('page',   String(params.page))
    if (params.limit)  q.set('limit',  String(params.limit))
    if (params.search) q.set('search', params.search)
    const qs = q.toString()
    return request<KeywordPage>(`/keywords${qs ? '?' + qs : ''}`)
  },

  addKeywords: (keywords: string[]): Promise<{ inserted: number; skipped: number; message: string }> =>
    request('/keywords', {
      method: 'POST',
      body: JSON.stringify({ keywords }),
    }),

  updateKeyword: (id: string, keyword: string): Promise<{ status: string; keyword: string }> =>
    request(`/keywords/${id}`, {
      method: 'PUT',
      body: JSON.stringify({ keyword }),
    }),

  deleteKeyword: (id: string): Promise<{ status: string; deleted: string }> =>
    request(`/keywords/${id}`, { method: 'DELETE' }),
}