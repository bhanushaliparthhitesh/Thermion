import { apiFetch } from './client'

/** Asks the Strands agent a question — it answers strictly from logged OpenSearch decisions. */
export function askAgent(question) {
  return apiFetch('/agent/ask', {
    method: 'POST',
    body: JSON.stringify({ question }),
  })
}
