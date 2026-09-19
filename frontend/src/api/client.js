const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:3000';

export async function runPipeline() {
  const response = await fetch(`${API_BASE}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  if (!response.ok) {
    throw new Error('Failed to run pipeline');
  }
  return response.json();
}

export async function getDecisions(limit = 20) {
  const response = await fetch(`${API_BASE}/decisions?limit=${limit}`);
  if (!response.ok) {
    throw new Error('Failed to fetch decisions');
  }
  return response.json();
}

export async function askAgent(question) {
  const response = await fetch(`${API_BASE}/agent/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question })
  });
  if (!response.ok) {
    throw new Error('Failed to ask agent');
  }
  return response.json();
}

// Added as fourth minimal function to keep getting a single decision explicitly cleanly separated from getDecisions.
export async function getDecisionById(stepId) {
  const response = await fetch(`${API_BASE}/decisions/${stepId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch decision details');
  }
  return response.json();
}
