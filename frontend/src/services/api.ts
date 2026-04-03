import type { AlertEvent, PipelineResult } from '../types/pipeline'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function analyzePipeline(event: AlertEvent): Promise<PipelineResult> {
  const res = await fetch(`${API_BASE}/ai/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(event),
  })
  if (!res.ok) {
    throw new Error(`Pipeline request failed: ${res.status} ${res.statusText}`)
  }
  return res.json()
}

export async function healthCheck(): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/health`)
    return res.ok
  } catch {
    return false
  }
}
