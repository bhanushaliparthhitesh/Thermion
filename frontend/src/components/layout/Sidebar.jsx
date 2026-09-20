import { NavLink } from 'react-router-dom'
import clsx from 'clsx'
import {
  LayoutGrid,
  Box,
  GitBranch,
  ShieldCheck,
  Activity,
  BarChart3,
  Bell,
  Bot,
  Settings,
} from 'lucide-react'

const NAV_ITEMS = [
  { to: '/', label: 'Command Center', icon: LayoutGrid, end: true },
  { to: '/digital-twin', label: 'Digital Twin', icon: Box },
  { to: '/decisions', label: 'AI Decisions', icon: GitBranch },
  { to: '/safety', label: 'Safety Center', icon: ShieldCheck },
  { to: '/telemetry', label: 'Live Telemetry', icon: Activity },
  { to: '/analytics', label: 'Analytics', icon: BarChart3 },
  { to: '/alerts', label: 'Alerts', icon: Bell },
]

function NavItem({ to, label, icon: Icon, end }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        clsx(
          'flex items-center gap-2.5 rounded-md px-3 py-2 text-sm transition-colors',
          isActive
            ? 'bg-primary-50 text-primary-700 font-medium'
            : 'text-ink-soft hover:bg-ink-faint/10 hover:text-ink',
        )
      }
    >
      <Icon size={17} strokeWidth={1.8} aria-hidden="true" />
      {label}
    </NavLink>
  )
}

export default function Sidebar({ collapsed }) {
  return (
    <aside
      className={clsx(
        'flex h-screen flex-col border-r border-border bg-card px-3 py-4 transition-all',
        collapsed ? 'w-[64px] items-center px-2' : 'w-[240px]',
      )}
    >
      <div className={clsx('mb-6 px-2', collapsed && 'px-0 text-center')}>
        {!collapsed ? (
          <>
            <p className="text-[15px] font-semibold tracking-tight text-ink">THERMION</p>
            <p className="text-[10.5px] font-medium uppercase tracking-wider text-ink-faint">
              AI Data Center Cooling
            </p>
          </>
        ) : (
          <p className="text-[15px] font-semibold text-primary-600">T</p>
        )}
      </div>

      <nav className="flex flex-1 flex-col gap-1">
        {NAV_ITEMS.map((item) => (
          <NavItem key={item.to} {...item} />
        ))}
      </nav>

      <div className="flex flex-col gap-1 border-t border-border pt-3">
        <NavItem to="/ask" label="Ask Thermion" icon={Bot} />
        <NavItem to="/settings" label="Settings" icon={Settings} />
      </div>
    </aside>
  )
}
