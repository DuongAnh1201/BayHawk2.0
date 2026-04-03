import type { WeatherResult } from '../types/pipeline'

const OWM_KEY = import.meta.env.VITE_OPENWEATHERMAP_API_KEY || ''
const OWM_URL = 'https://api.openweathermap.org/data/2.5/weather'

function spreadRisk(windSpeed: number, humidity: number): number {
  const windFactor = Math.min(windSpeed / 20, 1)
  const humidityFactor = Math.max(1 - humidity / 100, 0)
  return Math.round((windFactor * 0.6 + humidityFactor * 0.4) * 1000) / 1000
}

export interface LiveWeatherData {
  weather: WeatherResult
  latencyMs: number
}

export async function fetchLiveWeather(lat: number, lon: number): Promise<LiveWeatherData | null> {
  if (!OWM_KEY) return null

  const t0 = performance.now()

  try {
    const params = new URLSearchParams({
      lat: String(lat),
      lon: String(lon),
      appid: OWM_KEY,
      units: 'metric',
    })

    const res = await fetch(`${OWM_URL}?${params}`)
    const latencyMs = Math.round(performance.now() - t0)

    if (!res.ok) {
      console.warn(`OpenWeatherMap returned ${res.status}`)
      return null
    }

    const data = await res.json()

    const wind = data.wind ?? {}
    const main = data.main ?? {}
    const windSpeed: number = wind.speed ?? 0
    const windDirection: number = wind.deg ?? 0
    const humidity: number = main.humidity ?? 0

    return {
      weather: {
        wind_speed: windSpeed,
        wind_direction: windDirection,
        humidity,
        spread_risk: spreadRisk(windSpeed, humidity),
        raw: data,
        latency_ms: latencyMs,
      },
      latencyMs,
    }
  } catch (err) {
    console.warn('OpenWeatherMap fetch failed:', err)
    return null
  }
}

export function hasWeatherKey(): boolean {
  return OWM_KEY.length > 0
}
