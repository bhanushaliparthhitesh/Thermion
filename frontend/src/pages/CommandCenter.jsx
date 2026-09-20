import { ShieldCheck, Droplets, Fan, Cpu } from 'lucide-react'
import { useApi } from '../hooks/useApi'
import { getRecentDecisions } from '../api/decisions'
import { runPipeline } from '../api/pipeline'
import { useState } from 'react'

import KPICard from '../components/dashboard/KPICard'
import DataCenterOverview from '../components/dashboard/DataCenterOverview'
import LatestDecisionCard from '../components/dashboard/LatestDecisionCard'
import RecentDecisionsList from '../components/dashboard/RecentDecisionsList'
import StatusBadge from '../components/common/StatusBadge'
import LoadingState from '../components/common/LoadingState'
import ErrorState from '../components/common/ErrorState'
import Tooltip from '../components/common/Tooltip'

export default function CommandCenter() {
  const { data, status, error, refetch } = useApi(() => getRecentDecisions(10), [])
  const [running, setRunning] = useState(false)

  const decisions = data || []
  const latest = decisions[0]

  async function handleRun() {
    setRunning(true)
    try {
      await runPipeline(30)
      refetch()
    } catch {
      // surfaced via the error state on refetch if the backend is actually down
    } finally {
      setRunning(false)
    }
  }

  if (status === 'loading') return <LoadingState />
  if (status === 'error') return <ErrorState error={error} onRetry={refetch} />

  const safe = latest && latest.cedar_verdict?.allowed && !latest.safety_filter_verdict?.intervention_applied
  const waterTrend =
    decisions.length >= 2 ? decisions[0].state.water_usage - decisions[1].state.water_usage : null

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-ink">Command Center</h1>
          <p className="text-sm text-ink-soft">AI-powered real-time cooling operations</p>
        </div>
        <button
          onClick={handleRun}
          disabled={running}
          className="rounded-md bg-primary-600 px-3.5 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-60"
        >
          {running ? 'Running…' : 'Run pipeline'}
        </button>
      </div>

      {latest ? (
        <StatusBadge tone={safe ? 'safe' : 'warn'} className="w-fit text-sm">
          {safe ? 'System operational — safe' : 'Safety intervention active'}
        </StatusBadge>
      ) : (
        <StatusBadge tone="neutral" className="w-fit text-sm">
          No data yet
        </StatusBadge>
      )}

      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <KPICard
          icon={ShieldCheck}
          label="Hardware safety"
          value={latest ? latest.state.temperature_deviation : '—'}
          unit="° dev"
          status={
            latest && (
              <StatusBadge tone={safe ? 'safe' : 'critical'}>
                {safe ? 'Safe' : 'At risk'}
              </StatusBadge>
            )
          }
          rows={
            latest
              ? [{ label: 'Risk level', value: latest.safety_filter_verdict.risk_level }]
              : []
          }
        />

        <KPICard
          icon={Droplets}
          label="Water"
          value={latest ? latest.state.water_usage : '—'}
          rows={
            waterTrend !== null
              ? [{ label: 'Trend vs. last step', value: `${waterTrend >= 0 ? '+' : ''}${waterTrend.toFixed(2)}` }]
              : []
          }
        />

        <KPICard
          icon={Fan}
          label="Cooling strategy"
          value={latest ? latest.action_label : '—'}
          rows={
            latest
              ? [{ label: 'PPO proposed', value: latest.proposed_action_label }]
              : []
          }
        />

        <KPICard
          icon={Cpu}
          label={
            <span className="flex items-center gap-1">
              AI status <Tooltip label="Whether the last decision cycle ran and what Cedar decided." />
            </span>
          }
          status={
            latest && (
              <StatusBadge tone={latest.cedar_verdict.allowed ? 'safe' : 'critical'}>
                {latest.cedar_verdict.allowed ? 'Cedar allowed' : 'Cedar denied'}
              </StatusBadge>
            )
          }
          rows={
            latest
              ? [{ label: 'Last cycle', value: new Date(latest.timestamp).toLocaleTimeString() }]
              : []
          }
        />
      </div>

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
        <DataCenterOverview decision={latest} />
        <LatestDecisionCard decision={latest} />
      </div>

      <RecentDecisionsList decisions={decisions} />
    </div>
  )
}
