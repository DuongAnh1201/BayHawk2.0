const WINDY_API_KEY = import.meta.env.VITE_WINDY_API_KEY || ''
const WINDY_BASE = 'https://api.windy.com/webcams/api/v3/webcams'

export interface WindyWebcam {
  webcamId: string
  title: string
  images: {
    current: { preview: string; thumbnail: string }
    daylight: { preview: string; thumbnail: string }
  }
  location: {
    latitude: number
    longitude: number
    city: string
    region: string
    country: string
  }
}

interface WindyResponse {
  webcams: WindyWebcam[]
}

const imageCache = new Map<string, { webcams: WindyWebcam[]; ts: number }>()
const CACHE_TTL_MS = 8 * 60 * 1000 // refresh before 10-min token expiry

export async function fetchNearbyWebcams(
  lat: number,
  lon: number,
  radiusKm = 80,
  limit = 5,
): Promise<WindyWebcam[]> {
  if (!WINDY_API_KEY) return []

  const cacheKey = `${lat.toFixed(2)},${lon.toFixed(2)}`
  const cached = imageCache.get(cacheKey)
  if (cached && Date.now() - cached.ts < CACHE_TTL_MS) {
    return cached.webcams
  }

  try {
    const params = new URLSearchParams({
      nearby: `${lat},${lon},${radiusKm}`,
      include: 'images,location',
      limit: String(limit),
    })

    const res = await fetch(`${WINDY_BASE}?${params}`, {
      headers: { 'x-windy-api-key': WINDY_API_KEY },
    })

    if (!res.ok) {
      console.warn(`Windy API returned ${res.status}`)
      return []
    }

    const data: WindyResponse = await res.json()
    const webcams = data.webcams ?? []
    imageCache.set(cacheKey, { webcams, ts: Date.now() })
    return webcams
  } catch (err) {
    console.warn('Windy API fetch failed:', err)
    return []
  }
}

export function hasWindyKey(): boolean {
  return WINDY_API_KEY.length > 0
}
