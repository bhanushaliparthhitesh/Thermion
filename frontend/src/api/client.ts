import type { ApiDecision } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:3000';

type ApiResponse<T> = { ok: boolean; error?: string } & T;

async function errorFrom(response: Response): Promise<Error> {
  const text = await response.text();
  try {
    return new Error((JSON.parse(text) as { error?: string }).error || `Request failed with status ${response.status}`);
  } catch {
    return new Error(text || `Request failed with status ${response.status}`);
  }
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) throw await errorFrom(response);
  const body = (await response.json()) as ApiResponse<T>;
  if (!body.ok) throw new Error(body.error || 'The API rejected this request.');
  return body;
}

export async function getDecisions(): Promise<ApiDecision[]> {
  const body = await requestJson<{ decisions?: ApiDecision[] }>('/decisions?limit=25');
  if (!body.decisions) throw new Error('The API did not return a decisions array.');
  return body.decisions;
}

export async function getDecision(stepId: number): Promise<ApiDecision> {
  const body = await requestJson<{ decision?: ApiDecision }>(`/decisions/${stepId}`);
  if (!body.decision) throw new Error('The API did not return a decision.');
  return body.decision;
}

export async function runPipeline(): Promise<void> {
  const response = await fetch(`${API_BASE}/run`, { method: 'POST' });
  if (!response.ok) throw await errorFrom(response);
}

export async function askAgent(question: string): Promise<string> {
  const body = await requestJson<{ answer?: string }>('/agent/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question }),
  });
  if (!body.answer) throw new Error('The API did not return an answer.');
  return body.answer;
}
