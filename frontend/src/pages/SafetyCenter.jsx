import { Link } from 'react-router-dom'
import { useApi } from '../hooks/useApi'
import { getRecentDecisions } from '../api/decisions'
import StatusBadge from '../components/common/StatusBadge'
import LoadingState from '../components/common/LoadingState'
import ErrorState from '../components/common/ErrorState'
import EmptyState from '../components/common/EmptyState'

function isIntervention(d) {
  return !d.cedar_verdict?.allowed || d.safety_filter_verdict?.intervention_applied
}

function InterventionCard({ decision }) {
  return (
    <div className="card flex flex-col gap-2 border-warn-500/25 bg-warn-50/40 p-4">
      <p className="text-sm font-medium text-warn-700">Safety intervention — step #{decision.step_id}</p>
      <p className="text-xs text-ink-soft">Thermion prevented an unsafe cooling action.</p>

      <dl className="mt-1 flex flex-col gap-1.5 text-xs">
        <div className="flex justify-between">
          <dt className="text-ink-faint">AI proposed</dt>
          <dd className="font-mono text-ink">{decision.proposed_action_label}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-ink-faint">Cedar</dt>
          <dd>
            <StatusBadge tone={decision.cedar_verdict.allowed ? 'safe' : 'critical'}>
              {decision.cedar_verdict.allowed ? 'Allowed' : 'Denied'}
            </StatusBadge>
          </dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-ink-faint">Reason</dt>
          <dd className="max-w-[60%] text-right text-ink-soft">{decision.cedar_verdict.reason}</dd>
        </div>
        <div className="flex justify-between">
          <dt className="text-ink-faint">Final action</dt>
          <dd className="font-mono text-ink">{decision.action_label}</dd>
        </div>
      </dl>

      <Link to={`/decisions/${decision.step_id}`} className="mt-1 text-xs text-primary-600 hover:underline">
        View full decision →
      </Link>
    </div>
  )
}

export default function SafetyCenter() {
  const { data, status, error, refetch } = useApi(() => getRecentDecisions(50), [])

  if (status === 'loading') return <LoadingState />
  if (status === 'error') return <ErrorState error={error} onRetry={refetch} />

  const decisions = data || []
  const latest = decisions[0]
  const interventions = decisions.filter(isIntervention)
  const overallSafe = latest && !isIntervention(latest)

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-lg font-semibold text-ink">Safety Center</h1>
        <p className="text-sm text-ink-soft">Cedar policy and safety filter status</p>
      </div>

      <StatusBadge tone={latest ? (overallSafe ? 'safe' : 'warn') : 'neutral'} className="w-fit text-sm">
        {latest ? (overallSafe ? 'System safe' : 'Intervention active') : 'No data yet'}
      </StatusBadge>

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="card p-4">
          <p className="text-xs text-ink-faint">Cedar status</p>
          <p className="mt-1 font-mono text-ink">
            {latest ? (latest.cedar_verdict.allowed ? 'Allowing' : 'Denying') : '—'}
          </p>
        </div>
        <div className="card p-4">
          <p className="text-xs text-ink-faint">Safety filter</p>
          <p className="mt-1 font-mono text-ink">
            {latest ? (latest.safety_filter_verdict.intervention_applied ? 'Intervening' : 'Clear') : '—'}
          </p>
        </div>
        <div className="card p-4">
          <p className="text-xs text-ink-faint">Interventions (last {decisions.length} steps)</p>
          <p className="mt-1 font-mono text-ink">{interventions.length}</p>
        </div>
      </div>

      <div>
        <p className="mb-2 text-sm font-medium text-ink">Safety interventions</p>
        {interventions.length === 0 ? (
          <EmptyState
            title="No interventions in the recent window"
            hint="Cedar and the safety filter haven't had to override anything recently."
          />
        ) : (
          <div className="flex flex-col gap-3">
            {interventions.map((d) => (
              <InterventionCard key={d.step_id} decision={d} />
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
