import { apiFetch } from './client'

/** Runs the orchestrator loop for `steps` iterations — see run_local.py. */
export function runPipeline(steps = 30) {
  return apiFetch(`/run?steps=${steps}`, { method: 'POST' })
}
