import React, { useCallback, useEffect, useState } from 'react'

import {
  Database,
  Plus,
  Upload,
  X,
  Power,
  PowerOff,
  Search,
  Loader,
  Pencil,
  Trash2,
  Save,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
  XCircle,
} from 'lucide-react'

import { api } from '../api/client'

interface KeywordDoc {
  _id: string
  keyword: string
  enabled?: boolean
  created_at?: string
  last_crawled_at?: string | null
  crawl_count?: number
}

interface KeywordPage {
  items: KeywordDoc[]
  total: number
  page: number
  limit: number
}

const PAGE_LIMIT = 20

export default function KeywordsPage() {
  const [kwPage, setKwPage] = useState<KeywordPage | null>(null)
  const [kwLoading, setKwLoading] = useState(false)
  const [kwSearch, setKwSearch] = useState('')
  const [kwPageNum, setKwPageNum] = useState(1)
  const [kwError, setKwError] = useState<string | null>(null)
  const [addInput, setAddInput] = useState('')
  const [addLoading, setAddLoading] = useState(false)
  const [showAddBulk, setShowAddBulk] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')
  const [deleteId, setDeleteId] = useState<string | null>(null)
  const [deleteLoading, setDeleteLoading] = useState(false)
  const [togglingId, setTogglingId] = useState<string | null>(null)

  const loadKeywords = useCallback(
    async (page = kwPageNum, search = kwSearch) => {
      setKwLoading(true)
      setKwError(null)
      try {
        const data = await api.getKeywords({ page, limit: PAGE_LIMIT, search })
        setKwPage(data)
      } catch (e: any) {
        setKwError(e.message || 'Không thể tải keywords')
      } finally {
        setKwLoading(false)
      }
    },
    [kwPageNum, kwSearch]
  )

  useEffect(() => {
    loadKeywords(kwPageNum, kwSearch)
  }, [kwPageNum])

  useEffect(() => {
    const t = setTimeout(() => {
      setKwPageNum(1)
      loadKeywords(1, kwSearch)
    }, 400)
    return () => clearTimeout(t)
  }, [kwSearch])

  async function handleAddKeywords() {
    const lines = addInput.split('\n').map(k => k.trim()).filter(Boolean)
    if (!lines.length) return
    setAddLoading(true)
    try {
      await api.addKeywords(lines)
      setAddInput('')
      setShowAddBulk(false)
      setKwPageNum(1)
      await loadKeywords(1, kwSearch)
    } catch (e: any) {
      alert('Lỗi thêm keyword: ' + e.message)
    } finally {
      setAddLoading(false)
    }
  }

  async function handleEditSave(id: string) {
    const trimmed = editValue.trim()
    if (!trimmed) return
    try {
      await api.updateKeyword(id, trimmed)
      setEditingId(null)
      await loadKeywords()
    } catch (e: any) {
      alert('Lỗi sửa: ' + e.message)
    }
  }

  async function handleDelete(id: string) {
    setDeleteLoading(true)
    try {
      await api.deleteKeyword(id)
      setDeleteId(null)
      await loadKeywords()
    } catch (e: any) {
      alert('Lỗi xóa: ' + e.message)
    } finally {
      setDeleteLoading(false)
    }
  }

  async function handleToggle(id: string) {
    setTogglingId(id)
    try {
      await api.toggleKeyword(id)
      // Cập nhật local state ngay lập tức — không cần reload toàn bộ
      setKwPage(prev => {
        if (!prev) return prev
        return {
          ...prev,
          items: prev.items.map(kw =>
            kw._id === id ? { ...kw, enabled: !kw.enabled } : kw
          ),
        }
      })
    } catch (e: any) {
      alert('Lỗi bật/tắt keyword: ' + e.message)
    } finally {
      setTogglingId(null)
    }
  }

  const totalPages = kwPage ? Math.ceil(kwPage.total / PAGE_LIMIT) : 0
  const newLineCount = addInput.split('\n').filter(l => l.trim()).length

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold" style={{ color: 'var(--text-primary)' }}>
          Keywords
        </h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
          Quản lý keyword database
        </p>
      </div>

      <div
        className="rounded-2xl border p-6"
        style={{ background: 'var(--bg-card)', borderColor: 'var(--border)' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <Database className="w-6 h-6 text-violet-400" />
            <div>
              <h2 className="text-xl font-semibold">Keywords Database</h2>
              {kwPage && (
                <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
                  {kwPage.total.toLocaleString()} keywords
                </p>
              )}
            </div>
          </div>

          <button
            onClick={() => setShowAddBulk(v => !v)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-violet-600 hover:bg-violet-700 text-white font-medium transition-all"
          >
            {showAddBulk ? <X size={16} /> : <Plus size={16} />}
            {showAddBulk ? 'Đóng' : 'Thêm Keywords'}
          </button>
        </div>

        {/* Add bulk */}
        {showAddBulk && (
          <div
            className="mb-5 p-4 rounded-xl border"
            style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)' }}
          >
            <label
              className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-widest mb-2"
              style={{ color: 'var(--text-muted)' }}
            >
              <Upload size={12} />
              Nhập keywords
            </label>
            <textarea
              rows={5}
              value={addInput}
              onChange={e => setAddInput(e.target.value)}
              placeholder="Mỗi dòng một keyword..."
              className="w-full rounded-xl p-4 text-sm font-mono resize-y mb-3"
              style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--border)',
                color: 'var(--text-primary)',
              }}
            />
            <div className="flex items-center gap-3">
              <button
                onClick={handleAddKeywords}
                disabled={addLoading || !addInput.trim()}
                className="flex items-center gap-2 px-5 py-2.5 bg-violet-600 hover:bg-violet-700 disabled:opacity-50 rounded-xl font-medium text-white transition-all"
              >
                {addLoading ? <Loader size={16} className="animate-spin" /> : <Plus size={16} />}
                Thêm {newLineCount > 0 ? `${newLineCount} ` : ''}keywords
              </button>
              <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                Trùng sẽ tự bỏ qua
              </span>
            </div>
          </div>
        )}

        {/* Search */}
        <div className="relative mb-4">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            value={kwSearch}
            onChange={e => setKwSearch(e.target.value)}
            placeholder="Tìm keyword..."
            className="w-full rounded-xl pl-9 pr-4 py-2.5 text-sm"
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border)',
              color: 'var(--text-primary)',
            }}
          />
          {kwSearch && (
            <button
              onClick={() => setKwSearch('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500"
            >
              <X size={14} />
            </button>
          )}
        </div>

        {kwError && (
          <div className="flex items-center gap-2 p-3 rounded-xl mb-4 text-red-400 bg-red-900/20 border border-red-800 text-sm">
            <XCircle size={16} />
            {kwError}
          </div>
        )}

        {/* Table */}
        <div className="rounded-xl overflow-hidden border" style={{ borderColor: 'var(--border)' }}>
          {/* Header row */}
          <div
            className="grid text-xs font-semibold uppercase tracking-widest px-4 py-2.5"
            style={{
              gridTemplateColumns: '1fr 120px 110px 100px 100px',
              background: 'var(--bg-secondary)',
              color: 'var(--text-muted)',
            }}
          >
            <span>Keyword</span>
            <span>Ngày thêm</span>
            <span>Crawl</span>
            <span>Trạng thái</span>
            <span className="text-right">Hành động</span>
          </div>

          {kwLoading ? (
            <div className="flex items-center justify-center py-12 gap-3" style={{ color: 'var(--text-muted)' }}>
              <Loader size={20} className="animate-spin" />
              Đang tải...
            </div>
          ) : !kwPage || kwPage.items.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 gap-2" style={{ color: 'var(--text-muted)' }}>
              <Database size={32} className="opacity-30" />
              <p className="text-sm">Không có keyword</p>
            </div>
          ) : (
            <div className="divide-y" style={{ borderColor: 'var(--border)' }}>
              {kwPage.items.map(kw => {
                const isEnabled = kw.enabled !== false
                const isToggling = togglingId === kw._id

                return (
                  <div
                    key={kw._id}
                    className="grid items-center px-4 py-2.5 hover:bg-white/5 transition-colors"
                    style={{ gridTemplateColumns: '1fr 120px 110px 100px 100px' }}
                  >
                    {/* Keyword / Edit input */}
                    {editingId === kw._id ? (
                      <input
                        autoFocus
                        value={editValue}
                        onChange={e => setEditValue(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && handleEditSave(kw._id)}
                        className="rounded-lg px-3 py-1.5 text-sm mr-2"
                        style={{
                          background: 'var(--bg-secondary)',
                          border: '1px solid var(--accent)',
                          color: 'var(--text-primary)',
                        }}
                      />
                    ) : (
                      <span
                        className="text-sm font-mono truncate pr-2"
                        style={{
                          color: isEnabled ? 'var(--text-primary)' : 'var(--text-muted)',
                          textDecoration: isEnabled ? 'none' : 'line-through',
                          opacity: isEnabled ? 1 : 0.5,
                        }}
                      >
                        {kw.keyword}
                      </span>
                    )}

                    {/* Ngày thêm */}
                    <span className="text-xs" style={{ color: 'var(--text-muted)' }}>
                      {kw.created_at
                        ? new Date(kw.created_at).toLocaleDateString('vi-VN')
                        : '—'}
                    </span>

                    {/* Crawl count */}
                    <span className="text-xs">
                      {kw.last_crawled_at ? (
                        <span className="text-green-400">✓ {kw.crawl_count ?? 1}x</span>
                      ) : (
                        <span className="text-gray-600">Chưa crawl</span>
                      )}
                    </span>

                    {/* ✅ Toggle bật/tắt */}
                    <div>
                      <button
                        onClick={() => handleToggle(kw._id)}
                        disabled={isToggling}
                        title={isEnabled ? 'Đang bật — nhấn để tắt' : 'Đang tắt — nhấn để bật'}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all disabled:opacity-50"
                        style={{
                          background: isEnabled
                            ? 'rgba(34,197,94,0.15)'
                            : 'rgba(107,114,128,0.15)',
                          color: isEnabled ? '#4ade80' : '#6b7280',
                          border: `1px solid ${isEnabled ? 'rgba(34,197,94,0.3)' : 'rgba(107,114,128,0.3)'}`,
                        }}
                      >
                        {isToggling ? (
                          <Loader size={12} className="animate-spin" />
                        ) : isEnabled ? (
                          <Power size={12} />
                        ) : (
                          <PowerOff size={12} />
                        )}
                        {isEnabled ? 'Bật' : 'Tắt'}
                      </button>
                    </div>

                    {/* Hành động */}
                    <div className="flex items-center justify-end gap-1">
                      {editingId === kw._id ? (
                        <>
                          <button
                            onClick={() => handleEditSave(kw._id)}
                            className="p-1.5 rounded-lg text-green-400 hover:bg-green-900/20"
                          >
                            <Save size={14} />
                          </button>
                          <button
                            onClick={() => setEditingId(null)}
                            className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-800"
                          >
                            <X size={14} />
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            onClick={() => {
                              setEditingId(kw._id)
                              setEditValue(kw.keyword)
                            }}
                            className="p-1.5 rounded-lg hover:bg-white/10"
                            style={{ color: 'var(--text-muted)' }}
                          >
                            <Pencil size={14} />
                          </button>
                          <button
                            onClick={() => setDeleteId(kw._id)}
                            className="p-1.5 rounded-lg text-red-400 hover:bg-red-900/20"
                          >
                            <Trash2 size={14} />
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between mt-4 text-sm">
            <span style={{ color: 'var(--text-muted)' }}>
              Trang {kwPageNum}/{totalPages}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setKwPageNum(p => Math.max(1, p - 1))}
                disabled={kwPageNum === 1}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg border disabled:opacity-40"
                style={{ borderColor: 'var(--border)' }}
              >
                <ChevronLeft size={16} />
                Trước
              </button>
              <button
                onClick={() => setKwPageNum(p => Math.min(totalPages, p + 1))}
                disabled={kwPageNum === totalPages}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg border disabled:opacity-40"
                style={{ borderColor: 'var(--border)' }}
              >
                Sau
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Delete confirm modal */}
      {deleteId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div
            className="rounded-2xl border p-6 w-full max-w-sm mx-4"
            style={{ background: 'var(--bg-card)', borderColor: 'var(--border)' }}
          >
            <div className="flex items-center gap-3 mb-3">
              <div className="w-10 h-10 rounded-full bg-red-900/40 flex items-center justify-center">
                <AlertTriangle size={20} className="text-red-400" />
              </div>
              <div>
                <p className="font-semibold">Xác nhận xóa</p>
                <p className="text-sm text-gray-400">Không thể hoàn tác</p>
              </div>
            </div>
            <div className="flex gap-3 mt-5">
              <button
                onClick={() => setDeleteId(null)}
                className="flex-1 py-2.5 rounded-xl border"
                style={{ borderColor: 'var(--border)' }}
              >
                Hủy
              </button>
              <button
                onClick={() => handleDelete(deleteId)}
                disabled={deleteLoading}
                className="flex-1 py-2.5 rounded-xl bg-red-600 text-white flex items-center justify-center gap-2"
              >
                {deleteLoading ? <Loader size={16} className="animate-spin" /> : <Trash2 size={16} />}
                Xóa
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}