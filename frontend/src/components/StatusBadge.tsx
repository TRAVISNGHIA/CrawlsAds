import React from 'react'

interface Props {
  status: string
}

const STATUS_CONFIG: Record<string, { label: string; color: string; dot: string }> = {
  pending:   { label: 'Pending',   color: 'text-yellow-400 bg-yellow-400/10 border-yellow-400/30', dot: 'bg-yellow-400' },
  running:   { label: 'Running',   color: 'text-cyan-400 bg-cyan-400/10 border-cyan-400/30',       dot: 'bg-cyan-400 pulse-dot' },
  completed: { label: 'Completed', color: 'text-green-400 bg-green-400/10 border-green-400/30',    dot: 'bg-green-400' },
  failed:    { label: 'Failed',    color: 'text-red-400 bg-red-400/10 border-red-400/30',          dot: 'bg-red-400' },
}

export default function StatusBadge({ status }: Props) {
  const cfg = STATUS_CONFIG[status] || { label: status, color: 'text-gray-400 bg-gray-400/10 border-gray-400/30', dot: 'bg-gray-400' }
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border mono ${cfg.color}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
      {cfg.label}
    </span>
  )
}
