import { useParams, useNavigate } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { useApi } from '../hooks/useApi'
import { getRecentDecisions, getDecision } from '../api/decisions'
import StatusBadge from '../components/common/StatusBadge'
import LoadingState from '../components/common/LoadingState'
import ErrorState from '../components/common/ErrorState'
import EmptyState from '../components/common/EmptyState'

const STAGES = ['Telemetry', 'Digital twin', 'PPO', 'Cedar', 'Safety filter', 'Final action']

function DecisionPipeline({ decision }) {
  const cedarAllowed = decision.cedar_verdict?.allowed
  const fellBack = decision.proposed_action_label !== decision.action_label

  return (
    <div className="flex flex-wrap items-center gap-1.5 text-xs">
      {STAGES.map((stage, i) => (
        <span key={stage} className="flex items-center gap-1.5">
          <span className="rounded-md border border-border bg-canvas px-2 py-1 text-ink-soft">
            {stage}
          </span>
          {i < STAGES.length - 1 && <ArrowRight size={12} className="text-ink-faint" aria-hidden="true" />}
        </span>
      ))}
      <StatusBadge tone={cedarAllowed ? 'safe' : 'critical'} className="ml-2">
        {cedarAllowed ? 'Allowed' : 'Denied'}
      </StatusBadge>
      {fellBack && <StatusBadge tone="warn">Fallback used</StatusBadge>}
    </div>
  )
}

function DecisionDetail({ decision }) {
  const { state, safety_filter_verdict: safety, cedar_verdict: cedar } = decision
  return (
    <div className="card flex flex-col gap-4 p-4">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-ink">
          Decision #{decision.step_id} · <span className="text-ink-faint">{decision.timestamp}</span>
        </p>
      </div>

      <DecisionPipeline decision={decision} />

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <p className="mb-1.5 text-xs font-medium text-ink-soft">Input state</p>
          <dl className="flex flex-col gap-1 text-xs">
            {Object.entries(state).map(([k, v]) => (
              <div key={k} className="flex justify-between">
                <dt className="text-ink-faint">{k.replace(/_/g, ' ')}</dt>
                <dd className="font-mono text-ink">{v}</dd>
              </div>
            ))}
          </dl>
        </div>

        <div>
          <p className="mb-1.5 text-xs font-medium text-ink-soft">Safety filter</p>
          <dl className="flex flex-col gap-1 text-xs">
            <div className="flex justify-between">
              <dt className="text-ink-faint">Intervention applied</dt>
              <dd className="font-mono text-ink">{String(safety.intervention_applied)}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-ink-faint">Risk level</dt>
              <dd className="font-mono text-ink">{safety.risk_level}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-ink-faint">Risk score</dt>
              <dd className="font-mono text-ink">{safety.risk_score}</dd>
            </div>
          </dl>
          <p className="mt-2 text-xs text-ink-soft">{safety.reason}</p>
        </div>
      </div>

      <div className="border-t border-border pt-3">
        <p className="mb-1 text-xs font-medium text-ink-soft">Cedar verdict</p>
        <p className="text-xs text-ink-soft">{cedar.reason}</p>
      </div>

      {decision.strategy_reason && (
        <div className="border-t border-border pt-3">
          <p className="mb-1 text-xs font-medium text-ink-soft">Strategy reasoning</p>
          <p className="text-xs text-ink-soft">{decision.strategy_reason}</p>
        </div>
      )}
    </div>
  )
}

export default function AIDecisions() {
  const { stepId } = useParams()
  const navigate = useNavigate()

  const list = useApi(() => getRecentDecisions(25), [])
  const detail = useApi(() => getDecision(stepId), [stepId], { isEmpty: (d) => !d?.found })

  if (stepId) {
    if (detail.status === 'loading') return <LoadingState />
    if (detail.status === 'error') return <ErrorState error={detail.error} onRetry={detail.refetch} />
    if (detail.status === 'empty') {
      return <EmptyState title={`No decision found for step ${stepId}`} />
    }
    return (
      <div className="flex flex-col gap-4">
        <button onClick={() => navigate('/decisions')} className="w-fit text-xs text-primary-600 hover:underline">
          ← Back to all decisions
        </button>
        <DecisionDetail decision={detail.data} />
      </div>
    )
  }

  if (list.status === 'loading') return <LoadingState />
  if (list.status === 'error') return <ErrorState error={list.error} onRetry={list.refetch} />

  return (
    <div className="flex flex-col gap-5">
      <div>
        <h1 className="text-lg font-semibold text-ink">AI Decision Center</h1>
        <p className="text-sm text-ink-soft">How Thermion arrived at each cooling decision</p>
      </div>

      {list.status === 'empty' ? (
        <EmptyState title="No decisions logged yet" hint="Trigger a run from Command Center." />
      ) : (
        <div className="card divide-y divide-border">
          {list.data.map((d) => (
            <button
              key={d.step_id}
              onClick={() => navigate(`/decisions/${d.step_id}`)}
              className="flex w-full items-center justify-between gap-3 p-3 text-left text-sm hover:bg-ink-faint/5"
            >
              <span className="w-12 font-mono text-xs text-ink-faint">#{d.step_id}</span>
              <span className="flex-1">
                <DecisionPipeline decision={d} />
              </span>
              <span className="font-mono text-ink">{d.action_label}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
