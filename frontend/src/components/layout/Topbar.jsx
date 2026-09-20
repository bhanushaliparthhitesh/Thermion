import { useEffect, useState } from 'react'
import { Bell, Menu } from 'lucide-react'
import clsx from 'clsx'
import StatusBadge from '../common/StatusBadge'
import { useRole } from '../../context/RoleContext'

function useClock() {
  const [now, setNow] = useState(new Date())
  useEffect(() => {
    const id = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(id)
  }, [])
  return now
}

function formatTime(date) {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

/**
 * systemStatus: { tone: 'safe'|'warn'|'critical'|'neutral', label: string } — derived
 * from the latest decision's cedar/safety verdicts by the caller (CommandCenter),
 * not invented here.
 * lastUpdate: ISO timestamp string of the most recent logged decision, or null.
 */
export default function Topbar({ systemStatus, lastUpdate, onToggleSidebar }) {
  const now = useClock()
  const { role, setRole } = useRole()

  return (
    <header className="flex h-14 items-center justify-between border-b border-border bg-card px-5">
      <div className="flex items-center gap-4">
        <button
          onClick={onToggleSidebar}
          className="text-ink-soft hover:text-ink md:hidden"
          aria-label="Toggle navigation"
        >
          <Menu size={18} />
        </button>
        {systemStatus && <StatusBadge tone={systemStatus.tone}>{systemStatus.label}</StatusBadge>}
        <span className="hidden text-xs text-ink-faint sm:inline">
          Last update{' '}
          <span className="font-mono">
            {lastUpdate ? new Date(lastUpdate).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '—'}
          </span>
        </span>
      </div>

      <div className="flex items-center gap-4">
        <span className="hidden font-mono text-xs text-ink-soft sm:inline">{formatTime(now)}</span>

        <button className="relative text-ink-soft hover:text-ink" aria-label="Notifications">
          <Bell size={17} />
        </button>

        <div className="flex items-center rounded-md border border-border bg-canvas p-0.5 text-xs">
          {['operator', 'manager'].map((r) => (
            <button
              key={r}
              onClick={() => setRole(r)}
              className={clsx(
                'rounded px-2.5 py-1 font-medium capitalize transition-colors',
                role === r ? 'bg-card text-primary-700 shadow-card' : 'text-ink-soft',
              )}
            >
              {r}
            </button>
          ))}
        </div>
      </div>
    </header>
  )
}
