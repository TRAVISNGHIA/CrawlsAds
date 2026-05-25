import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard,
  Search,
  TableProperties,
  Radar,
  Database,
  Clock3,
  Play
} from 'lucide-react'


const links = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/manual-crawl', label: 'Crawl Thủ Công', icon: Play },
  { to: '/auto-crawl', label: 'Auto Crawl', icon: Clock3 },
  { to: '/keywords', label: 'Keywords', icon: Database },
  { to: '/results', label: 'Results', icon: TableProperties },
]

export default function Navbar() {
  return (
    <nav className="h-full flex flex-col border-r" style={{ borderColor: 'var(--border)', background: 'var(--bg-secondary)' }}>
      {/* Logo */}
      <div className="px-6 py-5 border-b flex items-center gap-3" style={{ borderColor: 'var(--border)' }}>
        <div className="w-8 h-8 rounded-lg flex items-center justify-center glow-accent" style={{ background: 'var(--accent)' }}>
          <Radar size={16} className="text-white" />
        </div>
        <div>
          <div className="text-sm font-bold tracking-wide" style={{ color: 'var(--text-primary)' }}>SEM</div>
          <div className="text-xs mono" style={{ color: 'var(--text-muted)' }}>CHECKER</div>
        </div>
      </div>

      {/* Nav links */}
      <div className="flex-1 px-3 py-4 flex flex-col gap-1">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150 group ${
                isActive
                  ? 'text-white'
                  : 'hover:text-white'
              }`
            }
            style={({ isActive }) => ({
              background: isActive ? 'var(--accent-dim)' : 'transparent',
              color: isActive ? 'white' : 'var(--text-secondary)',
              border: isActive ? '1px solid var(--accent-dim)' : '1px solid transparent',
            })}
          >
            <Icon size={15} />
            {label}
          </NavLink>
        ))}
      </div>

      {/* Version */}
      <div className="px-6 py-4 border-t" style={{ borderColor: 'var(--border)' }}>
        <p className="text-xs mono" style={{ color: 'var(--text-muted)' }}>v1.0.0</p>
      </div>
    </nav>
  )
}
