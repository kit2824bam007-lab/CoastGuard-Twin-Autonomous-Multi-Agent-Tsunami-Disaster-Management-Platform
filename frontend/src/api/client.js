// Central API client — set VITE_API_BASE_URL in .env for deployment
export const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/+$/, '')
export const WS_BASE = API_BASE.replace(/^http/, 'ws')

export function apiUrl(endpoint) {
  const clean = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  return `${API_BASE}${clean}`
}

export async function fetchEarthquakes(limit = 50) {
  const res = await fetch(`${API_BASE}/fetch-data/earthquakes?limit=${limit}`)
  if (!res.ok) throw new Error('Failed to fetch earthquakes')
  return res.json()
}

export async function fetchAlertHistory(limit = 50) {
  const res = await fetch(`${API_BASE}/alerts?limit=${limit}`)
  if (!res.ok) throw new Error('Failed to fetch alerts')
  return res.json()
}

export async function triggerIngestion() {
  const res = await fetch(`${API_BASE}/fetch-data/`, { method: 'POST' })
  if (!res.ok) throw new Error('Failed to trigger ingestion')
  return res.json()
}

export async function predictRisk(payload) {
  const res = await fetch(`${API_BASE}/predict-risk/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) throw new Error('Failed to run prediction')
  return res.json()
}

export function getAlertsWebSocketUrl() {
  return `${WS_BASE}/ws/alerts`
}

export async function fetchWaveForecast(earthquakeId) {
  const res = await fetch(`${API_BASE}/predict-risk/forecast/${earthquakeId}`)
  if (!res.ok) throw new Error(`Failed to fetch wave forecast for earthquake ${earthquakeId}`)
  return res.json()
}

export async function fetchSensorStations() {
  const res = await fetch(`${API_BASE}/sensors/`)
  if (!res.ok) throw new Error('Failed to fetch sensor stations')
  return res.json()
}

export async function fetchSensorReadings(stationId, limit = 50) {
  const res = await fetch(`${API_BASE}/sensors/readings/${stationId}?limit=${limit}`)
  if (!res.ok) throw new Error(`Failed to fetch readings for station ${stationId}`)
  return res.json()
}

export async function fetchCommandOverview(earthquakeId) {
  const res = await fetch(`${API_BASE}/command/overview/${earthquakeId}`)
  if (!res.ok) throw new Error(`Failed to fetch command overview for ${earthquakeId}`)
  return res.json()
}

export async function fetchSwarmPlan(earthquakeId) {
  const res = await fetch(`${API_BASE}/command/swarm/${earthquakeId}`)
  if (!res.ok) throw new Error(`Failed to fetch swarm plan for ${earthquakeId}`)
  return res.json()
}
