import { Link } from 'react-router-dom'
import StatusBadge from '../common/StatusBadge'
import EmptyState from '../common/EmptyState'

function outcomeOf(d) {
  if (!d.cedar_verdict?.allowed) return { tone: 'critical', glyph: '✕', label: 'Denied' }
  if (d.proposed_action_label !== d.action_label) return { tone: 'warn', glyph: '↩', label: 'Fallback' }
  return { tone: 'safe', glyph: '✓', label: 'Approved' }
}

export default function RecentDecisionsList({ decisions }) {
  if (!decisions || decisions.length === 0) {
    return (
      <div className="card p-4">
        <p className="mb-1 text-sm font-medium text-ink">Recent decisions</p>
        <EmptyState title="No decisions logged yet" hint="Trigger a run to populate this list." />
      </div>
    )
  }

  return (
    <div className="card p-4">
      <p className="mb-3 text-sm font-medium text-ink">Recent decisions</p>
      <ul className="flex flex-col divide-y divide-border">
        {decisions.map((d) => {
          const outcome = outcomeOf(d)
          return (
            <li key={d.step_id}>
              <Link
                to={`/decisions/${d.step_id}`}
                className="flex items-center justify-between gap-3 py-2.5 text-sm hover:bg-ink-faint/5"
              >
                <span className="flex items-center gap-3">
                  <span className="w-12 font-mono text-xs text-ink-faint">#{d.step_id}</span>
                  <span className="font-mono text-ink">{d.action_label}</span>
                </span>
                <StatusBadge tone={outcome.tone} glyph={outcome.glyph}>
                  {outcome.label}
                </StatusBadge>
              </Link>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
