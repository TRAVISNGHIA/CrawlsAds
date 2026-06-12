import React, { useEffect, useState } from 'react'
import {
  Clock, Loader, Power, PowerOff, Settings,
  Monitor, Smartphone, Tablet, CheckCircle,
  RefreshCcw, MapPin,
} from 'lucide-react'
import { api, LocationDoc, SchedulerConfig } from '../api/client'

const DEVICES = [
  { id: 'desktop', label: 'Desktop',  icon: Monitor    },
  { id: 'mobile',  label: 'Mobile',   icon: Smartphone },
  { id: 'tablet',  label: 'Tablet',   icon: Tablet     },
]

const DEFAULT_CONFIG: SchedulerConfig = {
  enabled: false,
  times_per_day: 4,
  devices: ['desktop'],
  profiles: ['Profile 44'],
  locations: [],
}

export default function AutoCrawlPage() {
  const [config, setConfig] = useState<SchedulerConfig>(DEFAULT_CONFIG)
  const [loading, setLoading] = useState(false)
  const [schedulerStatus, setSchedulerStatus] = useState<'running' | 'stopped'>('stopped')
  const [allLocations, setAllLocations] = useState<LocationDoc[]>([])
  const [locLoading, setLocLoading] = useState(false)

  async function loadConfig() {
    try {
      const data = await api.getSchedulerConfig()
      const normalized: SchedulerConfig = {
        enabled:       data.enabled       ?? false,
        times_per_day: data.times_per_day ?? 4,
        devices:       data.devices       ?? ['desktop'],
        profiles:      data.profiles      ?? ['Profile 44'],
        locations:     data.locations     ?? [],
      }
      setConfig(normalized)
      setSchedulerStatus(normalized.enabled ? 'running' : 'stopped')
    } catch (e) {
      console.error('Không tải được scheduler config:', e)
    }
  }

  async function loadLocations() {
    setLocLoading(true)
    try {
      const data = await api.getLocations()
      setAllLocations(data.items)
    } catch (e) {
      console.error('Không tải được locations:', e)
    } finally {
      setLocLoading(false)
    }
  }

  useEffect(() => {
    loadConfig()
    loadLocations()
  }, [])

  function toggleLocation(uule: string) {
    setConfig(prev => ({
      ...prev,
      locations: prev.locations.includes(uule)
        ? prev.locations.filter(u => u !== uule)
        : [...prev.locations, uule],
    }))
  }

  function selectAllLocations() {
    setConfig(prev => ({ ...prev, locations: allLocations.map(l => l.uule) }))
  }

  function clearLocations() {
    setConfig(prev => ({ ...prev, locations: [] }))
  }

  async function toggleScheduler() {
    const newEnabled = !config.enabled
    setLoading(true)
    try {
      const newConfig = { ...config, enabled: newEnabled }
      await api.updateSchedulerConfig(newConfig)
      setConfig(newConfig)
      setSchedulerStatus(newEnabled ? 'running' : 'stopped')
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  async function saveConfig() {
    setLoading(true)
    try {
      await api.updateSchedulerConfig(config)
      alert('Đã lưu cấu hình')
    } catch (e) {
      console.error(e)
      alert('Lưu thất bại')
    } finally {
      setLoading(false)
    }
  }

  const crawlEveryHours = Math.floor(24 / (config.times_per_day || 1))

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold" style={{ color: 'var(--text-primary)' }}>
          Auto Crawl
        </h1>
        <p className="text-sm mt-2" style={{ color: 'var(--text-muted)' }}>
          Scheduler sẽ tự động crawl các keyword đang bật ON
        </p>
      </div>

      <div className="rounded-2xl border p-6" style={{ background: 'var(--bg-card)', borderColor: 'var(--border)' }}>

        {/* Header + toggle */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <div className="w-14 h-14 rounded-2xl bg-blue-500/15 flex items-center justify-center">
              <Clock className="w-7 h-7 text-blue-400" />
            </div>
            <div>
              <h2 className="text-2xl font-semibold">Scheduler</h2>
              <p className="text-sm mt-1" style={{ color: 'var(--text-muted)' }}>Chạy tự động liên tục</p>
            </div>
          </div>
          <button
            onClick={toggleScheduler}
            disabled={loading}
            className={`flex items-center gap-2 px-5 py-3 rounded-xl font-semibold transition-all ${
              schedulerStatus === 'running' ? 'bg-green-600 text-white' : 'bg-zinc-700 text-zinc-300'
            }`}
          >
            {loading ? (
              <Loader size={18} className="animate-spin" />
            ) : schedulerStatus === 'running' ? (
              <PowerOff size={18} />
            ) : (
              <Power size={18} />
            )}
            {schedulerStatus === 'running' ? 'Đang chạy' : 'Đã tắt'}
          </button>
        </div>

        {/* Row 1: Số lần crawl + Profiles */}
        <div className="grid md:grid-cols-2 gap-5 mb-5">
          <div className="rounded-2xl border p-5" style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)' }}>
            <div className="flex items-center gap-2 mb-3">
              <RefreshCcw size={18} className="text-violet-400" />
              <h3 className="font-semibold">Số lần crawl / ngày</h3>
            </div>
            <input
              type="number"
              min={1}
              max={24}
              value={config.times_per_day}
              onChange={e => setConfig(prev => ({ ...prev, times_per_day: parseInt(e.target.value) || 1 }))}
              className="w-full rounded-xl px-4 py-3 text-lg"
              style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}
            />
            <p className="text-xs mt-3" style={{ color: 'var(--text-muted)' }}>
              Hệ thống sẽ chạy khoảng{' '}
              <span className="text-blue-400 font-semibold">mỗi {crawlEveryHours} giờ</span>
            </p>
          </div>

          <div className="rounded-2xl border p-5" style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)' }}>
            <h3 className="font-semibold mb-3">Profiles</h3>
            <input
              value={config.profiles.join(', ')}
              onChange={e =>
                setConfig(prev => ({
                  ...prev,
                  profiles: e.target.value.split(',').map(s => s.trim()).filter(Boolean),
                }))
              }
              placeholder="Profile 44, Profile 45"
              className="w-full rounded-xl px-4 py-3"
              style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}
            />
            <p className="text-xs mt-3" style={{ color: 'var(--text-muted)' }}>
              Có thể nhập nhiều profile, cách nhau bởi dấu phẩy
            </p>
          </div>
        </div>

        {/* Row 2: Devices */}
        <div className="rounded-2xl border p-5 mb-5" style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)' }}>
          <h3 className="font-semibold mb-4">Devices</h3>
          <div className="flex gap-3">
            {DEVICES.map(({ id, label, icon: Icon }) => {
              const active = config.devices.includes(id)
              return (
                <button
                  key={id}
                  onClick={() =>
                    setConfig(prev => ({
                      ...prev,
                      devices: active ? prev.devices.filter(d => d !== id) : [...prev.devices, id],
                    }))
                  }
                  className="flex-1 flex items-center justify-center gap-2 px-5 py-4 rounded-xl border transition-all"
                  style={{
                    background:  active ? 'var(--accent-dim)' : 'var(--bg-card)',
                    borderColor: active ? 'var(--accent)'     : 'var(--border)',
                    color:       active ? 'white'             : 'var(--text-secondary)',
                  }}
                >
                  <Icon size={18} />
                  {label}
                  {active && <CheckCircle size={15} />}
                </button>
              )
            })}
          </div>
        </div>

        {/* Row 3: Locations */}
        <div className="rounded-2xl border p-5 mb-6" style={{ background: 'var(--bg-secondary)', borderColor: 'var(--border)' }}>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <MapPin size={18} className="text-emerald-400" />
              <h3 className="font-semibold">Locations</h3>
              {config.locations.length > 0 && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400">
                  {config.locations.length} đã chọn
                </span>
              )}
            </div>
            {allLocations.length > 0 && (
              <div className="flex gap-2">
                <button
                  onClick={selectAllLocations}
                  className="text-xs px-3 py-1.5 rounded-lg transition-all"
                  style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-secondary)' }}
                >
                  Chọn tất cả
                </button>
                <button
                  onClick={clearLocations}
                  className="text-xs px-3 py-1.5 rounded-lg transition-all"
                  style={{ background: 'var(--bg-card)', border: '1px solid var(--border)', color: 'var(--text-muted)' }}
                >
                  Bỏ chọn
                </button>
              </div>
            )}
          </div>

          {locLoading ? (
            <div className="flex items-center gap-2 py-4" style={{ color: 'var(--text-muted)' }}>
              <Loader size={16} className="animate-spin" />
              <span className="text-sm">Đang tải locations...</span>
            </div>
          ) : allLocations.length === 0 ? (
            <div className="text-center py-6" style={{ color: 'var(--text-muted)' }}>
              <MapPin size={28} className="mx-auto mb-2 opacity-30" />
              <p className="text-sm">Chưa có location nào.</p>
              <p className="text-xs mt-1">
                Thêm ở trang Locations trong menu bên trái
              </p>
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">
              {allLocations.map(loc => {
                const active = config.locations.includes(loc.uule)
                return (
                  <button
                    key={loc._id}
                    onClick={() => toggleLocation(loc.uule)}
                    title={loc.uule}
                    className="flex items-center gap-1.5 px-3 py-2 rounded-xl border text-sm transition-all"
                    style={{
                      background:  active ? 'rgba(52,211,153,0.15)' : 'var(--bg-card)',
                      borderColor: active ? 'rgba(52,211,153,0.5)'  : 'var(--border)',
                      color:       active ? '#34d399'                : 'var(--text-secondary)',
                    }}
                  >
                    <MapPin size={13} />
                    {loc.name}
                    {active && <CheckCircle size={13} />}
                  </button>
                )
              })}
            </div>
          )}

          <p className="text-xs mt-3" style={{ color: 'var(--text-muted)' }}>
            {config.locations.length === 0
              ? 'Không chọn location → crawl không giả lập vị trí'
              : `Crawler sẽ chạy ${config.locations.length} location x tất cả keywords`}
          </p>
        </div>

        {/* Save */}
        <button
          onClick={saveConfig}
          disabled={loading}
          className="w-full py-4 rounded-2xl bg-blue-600 hover:bg-blue-700 text-white font-semibold flex items-center justify-center gap-2 transition-all"
        >
          {loading ? <Loader size={18} className="animate-spin" /> : <Settings size={18} />}
          Lưu cấu hình Auto Crawl
        </button>
      </div>
    </div>
  )
}