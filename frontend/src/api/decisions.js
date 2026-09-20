import { apiFetch } from './client'

/** Most recent n decisions, newest first — matches strands_agent/tools.py's query_recent_decisions. */
export function getRecentDecisions(n = 10) {
  return apiFetch(`/decisions?n=${n}`)
}

/** One decision by step_id — matches strands_agent/tools.py's explain_decision. */
export function getDecision(stepId) {
  return apiFetch(`/decisions/${stepId}`)
}
