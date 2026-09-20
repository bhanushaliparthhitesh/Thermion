import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import Topbar from './Topbar'
import { useApi } from '../../hooks/useApi'
import { getRecentDecisions } from '../../api/decisions'

/** Turns the latest logged decision into a topbar status pill — no fabricated health metric. */
function deriveSystemStatus(latest) {
  if (!latest) return { tone: 'neutral', label: 'No data' }
  const safe = latest.cedar_verdict?.allowed && !latest.safety_filter_verdict?.intervention_applied
  return safe
    ? { tone: 'safe', label: 'System safe' }
    : { tone: 'warn', label: 'Safety intervention active' }
}

export default function AppShell() {
  const [collapsed, setCollapsed] = useState(false)
  const { data } = useApi(() => getRecentDecisions(1), [])
  const latest = Array.isArray(data) ? data[0] : null

  return (
    <div className="flex">
      <Sidebar collapsed={collapsed} />
      <div className="flex min-h-screen flex-1 flex-col">
        <Topbar
          systemStatus={deriveSystemStatus(latest)}
          lastUpdate={latest?.timestamp}
          onToggleSidebar={() => setCollapsed((c) => !c)}
        />
        <main className="flex-1 overflow-y-auto bg-canvas p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
