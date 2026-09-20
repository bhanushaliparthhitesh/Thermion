import { ArrowRight } from 'lucide-react'
import StatusBadge from '../common/StatusBadge'
import EmptyState from '../common/EmptyState'

export default function LatestDecisionCard({ decision }) {
  if (!decision) {
    return (
      <div className="card p-4">
        <p className="mb-1 text-sm font-medium text-ink">Latest AI decision</p>
        <EmptyState
          title="No decisions logged yet"
          hint="Run the pipeline to see the first decision appear here."
        />
      </div>
    )
  }

  const wasOverridden = decision.proposed_action_label !== decision.action_label
  const cedarAllowed = decision.cedar_verdict?.allowed

  return (
    <div className="card flex flex-col gap-3 p-4">
      <p className="text-sm font-medium text-ink">Latest AI decision</p>

      <div className="flex flex-col gap-2 text-sm">
        <div className="flex items-center justify-between">
          <span className="text-ink-faint">PPO proposed</span>
          <span className="font-mono font-medium text-ink">{decision.proposed_action_label}</span>
        </div>

        <div className="flex items-center justify-between">
          <span className="text-ink-faint">Cedar</span>
          <StatusBadge tone={cedarAllowed ? 'safe' : 'critical'} glyph={cedarAllowed ? '✓' : '✕'}>
            {cedarAllowed ? 'Allowed' : 'Denied'}
          </StatusBadge>
        </div>

        {wasOverridden && (
          <div className="flex items-center justify-between">
            <span className="text-ink-faint">Fallback</span>
            <span className="font-mono font-medium text-warn-700">{decision.action_label}</span>
          </div>
        )}

        <div className="flex items-center justify-between border-t border-border pt-2">
          <span className="flex items-center gap-1 font-medium text-ink-soft">
            Final action <ArrowRight size={12} aria-hidden="true" />
          </span>
          <span className="font-mono text-base font-semibold text-ink">{decision.action_label}</span>
        </div>
      </div>

      {decision.strategy_reason && (
        <p className="border-t border-border pt-2.5 text-xs leading-relaxed text-ink-soft">
          {decision.strategy_reason}
        </p>
      )}
    </div>
  )
}
