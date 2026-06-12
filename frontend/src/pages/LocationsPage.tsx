import React, { useEffect, useState } from 'react'
import {
  MapPin, Plus, X, Loader, Pencil, Trash2, Save,
  AlertTriangle, XCircle, ExternalLink, Copy, Check,
} from 'lucide-react'
import { api, LocationDoc } from '../api/client'

export default function LocationsPage() {
  const [locations, setLocations]         = useState<LocationDoc[]>([])
  const [loading, setLoading]             = useState(false)
  const [error, setError]                 = useState<string | null>(null)
  const [showAdd, setShowAdd]             = useState(false)
  const [addName, setAddName]             = useState('')
  const [addUule, setAddUule]             = useState('')
  const [addLoading, setAddLoading]       = useState(false)
  const [editingId, setEditingId]         = useState<string | null>(null)
  const [editName, setEditName]           = useState('')
  const [editUule, setEditUule]           = useState('')
  const [deleteId, setDeleteId]           = useState<string | null>(null)
  const [deleteLoading, setDeleteLoading] = useState(false)
  const [copiedId, setCopiedId]           = useState<string | null>(null)

  async function loadLocations() {
    setLoading(true)
    setError(null)
    try {
      const data = await api.getLocations()
      setLocations(data.items)
    } catch (e: any) {
      setError(e.message || 'Không thể tải locations')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadLocations() }, [])

  async function handleAdd() {
    const name = addName.trim()
    const uule = addUule.trim()
    if (!name || !uule) return
    setAddLoading(true)
    try {
      await api.addLocation(uule, name)
      setAddName('')
      setAddUule('')
      setShowAdd(false)
      await loadLocations()
    } catch (e: any) {
      alert('Lỗi thêm location: ' + e.message)
    } finally {
      setAddLoading(false)
    }
  }

  async function handleEditSave(id: string) {
    const name = editName.trim()
    const uule = editUule.trim()
    if (!name || !uule) return
    try {
      await api.updateLocation(id, { name, uule })
      setEditingId(null)
      await loadLocations()
    } catch (e: any) {
      alert('Lỗi cập nhật: ' + e.message)
    }
  }

  async function handleDelete(id: string) {
    setDeleteLoading(true)
    try {
      await api.deleteLocation(id)
      setDeleteId(null)
      await loadLocations()
    } catch (e: any) {
      alert('Lỗi xóa: ' + e.message)
    } finally {
      setDeleteLoading(false)
    }
  }

  async function handleCopyUule(id: string, uule: string) {
    await navigator.clipboard.writeText(uule)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 1500)
  }

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold" style={{ color: 'var(--text-primary)' }}>
          Locations
        </h1>
        <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>
          Quản lý danh sách địa điểm để giả lập vị trí khi crawl Google Search
        </p>
      </div>

      <div className="rounded-2xl border p-6" style={{ background: 'var(--bg-card)', borderColor: 'var(--border)' }}>

        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <MapPin className="w-6 h-6 text-emerald-400" />
            <div>
              <h2 className="text-xl font-semibold">Locations Database</h2>
              <p className="text-xs mt-0.5" style={{ color: 'var(--text-muted)' }}>
                {locations.length} location{locations.length !== 1 ? 's' : ''}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <a
              href="https://www.indexguru.io/uule-generator"
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm transition-all"
              style={{ background: 'var(--bg-secondary)', border: '1px solid var(--border)', color: 'var(--text-muted)' }}
            >
              <ExternalLink size={14} />
              UULE Generator
            </a>
            <button
              onClick={() => setShowAdd(v => !v)}
              className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-medium transition-all"
            >
              {showAdd ? <X size={16} /> : <Plus size={16} />}
              {showAdd ? 'Đóng' : 'Thêm Location'}
            </button>
          </div>
        </div>

        {showAdd && (
          <div className="mb-5 p-5 rounded-xl border" style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)' }}>
            <p className="text-xs font-semibold uppercase tracking-widest mb-4" style={{ color: 'var(--text-muted)' }}>
              Thêm location mới
            </p>

            <div className="grid md:grid-cols-2 gap-4 mb-4">
              <div>
                <p className="text-xs mb-1.5" style={{ color: 'var(--text-muted)' }}>Tên địa điểm</p>
                <input
                  value={addName}
                  onChange={e => setAddName(e.target.value)}
                  placeholder="vd: Hà Nội, Đà Nẵng, TP.HCM"
                  className="w-full rounded-xl px-4 py-3 text-sm"
                  style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}
                />
              </div>
              <div>
                <p className="text-xs mb-1.5" style={{ color: 'var(--text-muted)' }}>
                  UULE code — lấy tại indexguru.io/uule-generator
                </p>
                <input
                  value={addUule}
                  onChange={e => setAddUule(e.target.value)}
                  placeholder="w+CAIQICIFSGFub2k"
                  className="w-full rounded-xl px-4 py-3 text-sm font-mono"
                  style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}
                />
              </div>
            </div>

            <div
              className="rounded-xl p-3 mb-4 text-xs"
              style={{ background: 'rgba(52,211,153,0.07)', border: '1px solid rgba(52,211,153,0.2)', color: 'var(--text-muted)' }}
            >
              <span className="text-emerald-400 font-semibold">Cách lấy UULE: </span>
              Vào Google Maps, tìm địa điểm, copy tên đầy đủ (vd: Da Nang, Hai Chau District, Da Nang),
              dán vào indexguru.io/uule-generator, copy mã w+...
            </div>

            <button
              onClick={handleAdd}
              disabled={addLoading || !addName.trim() || !addUule.trim()}
              className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 rounded-xl font-medium text-white transition-all"
            >
              {addLoading ? <Loader size={16} className="animate-spin" /> : <Plus size={16} />}
              Thêm location
            </button>
          </div>
        )}

        {error && (
          <div className="flex items-center gap-2 p-3 rounded-xl mb-4 text-red-400 bg-red-900/20 border border-red-800 text-sm">
            <XCircle size={16} />
            {error}
          </div>
        )}

        <div className="rounded-xl overflow-hidden border" style={{ borderColor: 'var(--border)' }}>
          <div
            className="grid text-xs font-semibold uppercase tracking-widest px-4 py-2.5"
            style={{ gridTemplateColumns: '180px 1fr 110px', background: 'var(--bg-secondary)', color: 'var(--text-muted)' }}
          >
            <span>Tên địa điểm</span>
            <span>UULE Code</span>
            <span className="text-right">Hành động</span>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-12 gap-3" style={{ color: 'var(--text-muted)' }}>
              <Loader size={20} className="animate-spin" />
              Đang tải...
            </div>
          ) : locations.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 gap-2" style={{ color: 'var(--text-muted)' }}>
              <MapPin size={32} className="opacity-30" />
              <p className="text-sm">Chưa có location nào</p>
              <p className="text-xs">Nhấn "Thêm Location" để bắt đầu</p>
            </div>
          ) : (
            <div className="divide-y" style={{ borderColor: 'var(--border)' }}>
              {locations.map(loc => (
                <div
                  key={loc._id}
                  className="grid items-center px-4 py-3 hover:bg-white/5 transition-colors"
                  style={{ gridTemplateColumns: '180px 1fr 110px' }}
                >
                  {editingId === loc._id ? (
                    <input
                      autoFocus
                      value={editName}
                      onChange={e => setEditName(e.target.value)}
                      className="rounded-lg px-3 py-1.5 text-sm mr-2"
                      style={{ background: 'var(--bg-secondary)', border: '1px solid var(--accent)', color: 'var(--text-primary)' }}
                    />
                  ) : (
                    <div className="flex items-center gap-2 pr-2">
                      <MapPin size={13} className="text-emerald-400 shrink-0" />
                      <span className="text-sm font-medium truncate" style={{ color: 'var(--text-primary)' }}>
                        {loc.name}
                      </span>
                    </div>
                  )}

                  {editingId === loc._id ? (
                    <input
                      value={editUule}
                      onChange={e => setEditUule(e.target.value)}
                      className="rounded-lg px-3 py-1.5 text-sm font-mono mr-2"
                      style={{ background: 'var(--bg-secondary)', border: '1px solid var(--accent)', color: 'var(--text-primary)' }}
                    />
                  ) : (
                    <div className="flex items-center gap-2 pr-2">
                      <span className="text-xs font-mono truncate" style={{ color: 'var(--text-muted)' }} title={loc.uule}>
                        {loc.uule}
                      </span>
                      <button
                        onClick={() => handleCopyUule(loc._id, loc.uule)}
                        title="Copy UULE"
                        className="p-1 rounded shrink-0 hover:text-emerald-400 transition-colors"
                        style={{ color: copiedId === loc._id ? '#34d399' : 'var(--text-muted)' }}
                      >
                        {copiedId === loc._id ? <Check size={13} /> : <Copy size={13} />}
                      </button>
                    </div>
                  )}

                  <div className="flex items-center justify-end gap-1">
                    {editingId === loc._id ? (
                      <>
                        <button onClick={() => handleEditSave(loc._id)} className="p-1.5 rounded-lg text-green-400 hover:bg-green-900/20">
                          <Save size={14} />
                        </button>
                        <button onClick={() => setEditingId(null)} className="p-1.5 rounded-lg text-gray-500 hover:bg-gray-800">
                          <X size={14} />
                        </button>
                      </>
                    ) : (
                      <>
                        <button
                          onClick={() => { setEditingId(loc._id); setEditName(loc.name); setEditUule(loc.uule) }}
                          className="p-1.5 rounded-lg hover:bg-white/10"
                          style={{ color: 'var(--text-muted)' }}
                        >
                          <Pencil size={14} />
                        </button>
                        <button onClick={() => setDeleteId(loc._id)} className="p-1.5 rounded-lg text-red-400 hover:bg-red-900/20">
                          <Trash2 size={14} />
                        </button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {deleteId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="rounded-2xl border p-6 w-full max-w-sm mx-4" style={{ background: 'var(--bg-card)', borderColor: 'var(--border)' }}>
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