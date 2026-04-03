export type ConfirmationStatus = 'CONFIRMED' | 'DISMISSED'
export type CriticalityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export interface AlertEvent {
  event_id: string
  lat: number
  lon: number
  camera_id?: string
  image_url?: string
  timestamp: string
}

export interface CameraResult {
  confidence: number
  detected: boolean
  image_url?: string | null
  raw?: Record<string, unknown> | null
  latency_ms?: number | null
  telemetry?: Record<string, unknown> | null
}

export interface SatelliteResult {
  thermal_confidence: number
  hotspot_detected: boolean
  raw?: Record<string, unknown> | null
  latency_ms?: number | null
  telemetry?: Record<string, unknown> | null
}

export interface WeatherResult {
  wind_speed: number
  wind_direction: number
  humidity: number
  spread_risk: number
  raw?: Record<string, unknown> | null
  latency_ms?: number | null
  telemetry?: Record<string, unknown> | null
}

export interface FusionResult {
  status: ConfirmationStatus
  combined_score: number
  reason: string
  telemetry?: Record<string, unknown> | null
}

export interface ReasoningResult {
  scene_description: string
  key_observations: string[]
}

export interface ClassificationResult {
  criticality: CriticalityLevel
  score: number
  reasoning: string
}

export interface SuggestionResult {
  action_plan: string[]
  alert_message: string
  recommended_resources: string[]
}

export interface OutputResult {
  notification_sent: boolean
  dashboard_updated: boolean
  incident_id: string
  logged: boolean
}

export interface PipelineResult {
  event_id: string
  camera?: CameraResult | null
  satellite?: SatelliteResult | null
  weather?: WeatherResult | null
  fusion?: FusionResult | null
  reasoning?: ReasoningResult | null
  classification?: ClassificationResult | null
  suggestion?: SuggestionResult | null
  output?: OutputResult | null
  error?: string | null
}

export interface CameraNode {
  id: string
  name: string
  code: string
  lat: number
  lon: number
  online: boolean
  alertcaId?: string
}
