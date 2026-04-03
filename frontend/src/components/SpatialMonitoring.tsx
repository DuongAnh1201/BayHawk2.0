import { useState, useMemo } from 'react'
import { MapContainer, TileLayer, Marker, Popup, CircleMarker } from 'react-leaflet'
import { Icon } from 'leaflet'
import { Map as MapIcon } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import { usePipeline } from '../context/PipelineContext'

const cameraIcon = new Icon({
  iconUrl:
    'data:image/svg+xml,' +
    encodeURIComponent(
      `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="10" fill="#2563eb" stroke="white" stroke-width="2"/>
        <circle cx="12" cy="12" r="4" fill="white"/>
      </svg>`,
    ),
  iconSize: [24, 24],
  iconAnchor: [12, 12],
})

const activeIcon = new Icon({
  iconUrl:
    'data:image/svg+xml,' +
    encodeURIComponent(
      `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 28 28">
        <circle cx="14" cy="14" r="12" fill="#d97706" stroke="white" stroke-width="2"/>
        <circle cx="14" cy="14" r="5" fill="white"/>
      </svg>`,
    ),
  iconSize: [28, 28],
  iconAnchor: [14, 14],
})

const droneReadyIcon = new Icon({
  iconUrl:
    'data:image/svg+xml,' +
    encodeURIComponent(
      `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 28 28">
        <rect x="2" y="2" width="24" height="24" rx="6" fill="#059669" stroke="white" stroke-width="2"/>
        <path d="M8 14h12M14 8v12M9 9l2 2M17 9l-2 2M9 19l2-2M17 19l-2-2" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
      </svg>`,
    ),
  iconSize: [28, 28],
  iconAnchor: [14, 14],
})

const droneDeployedIcon = new Icon({
  iconUrl:
    'data:image/svg+xml,' +
    encodeURIComponent(
      `<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 28 28">
        <rect x="2" y="2" width="24" height="24" rx="6" fill="#dc2626" stroke="white" stroke-width="2"/>
        <path d="M8 14h12M14 8v12M9 9l2 2M17 9l-2 2M9 19l2-2M17 19l-2-2" stroke="white" stroke-width="1.5" stroke-linecap="round"/>
      </svg>`,
    ),
  iconSize: [28, 28],
  iconAnchor: [14, 14],
})

type LayerOption = 'dark' | 'satellite' | 'streets'

const TILE_LAYERS: Record<LayerOption, { url: string; attribution: string }> = {
  dark: {
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>',
  },
  satellite: {
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: '&copy; Esri',
  },
  streets: {
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  },
}

export default function SpatialMonitoring() {
  const { theme } = useTheme()
  const dark = theme === 'dark' || theme === 'verizon'
  const { cameras, selectedCamera, pipelineResult, droneStations, droneDispatches } = usePipeline()
  const [layer, setLayer] = useState<LayerOption>('dark')

  const hotspots = useMemo(() => {
    const raw = pipelineResult?.satellite?.raw as Record<string, unknown> | null | undefined
    if (!raw) return []
    const list = raw.hotspots
    if (!Array.isArray(list)) return []
    return list.filter(
      (h): h is { latitude: number; longitude: number; frp: number } =>
        typeof h === 'object' && h !== null && 'latitude' in h && 'longitude' in h,
    )
  }, [pipelineResult])

  return (
    <div className={`rounded-xl border overflow-hidden flex flex-col h-full ${dark ? 'bg-[#111] border-[#1e1e1e]' : 'bg-white border-gray-200'}`}>
      <div className={`flex items-center justify-between px-4 py-2.5 border-b shrink-0 ${dark ? 'border-[#1e1e1e]' : 'border-gray-100'}`}>
        <div className="flex items-center gap-2">
          <MapIcon className={`h-4 w-4 ${dark ? 'text-gray-500' : 'text-gray-400'}`} />
          <span className={`text-sm font-semibold uppercase tracking-wider ${dark ? 'text-gray-400' : 'text-gray-600'}`}>
            Spatial Monitoring
          </span>
          {hotspots.length > 0 && (
            <span className="text-xs font-bold text-red-400 bg-red-400/10 rounded px-2 py-0.5">
              {hotspots.length} hotspot{hotspots.length > 1 ? 's' : ''}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-xs ${dark ? 'text-gray-500' : 'text-gray-400'}`}>Layer</span>
          <select
            value={layer}
            onChange={e => setLayer(e.target.value as LayerOption)}
            className={`text-xs rounded-md px-2 py-1.5 outline-none cursor-pointer ${
              dark
                ? 'bg-[#1a1a1a] text-gray-300 border border-[#2a2a2a]'
                : 'bg-gray-100 text-gray-700 border border-gray-200'
            }`}
          >
            <option value="dark">Dark Topo</option>
            <option value="satellite">Satellite</option>
            <option value="streets">Streets</option>
          </select>
        </div>
      </div>

      <div className="flex-1 min-h-0">
        <MapContainer
          center={[34.2, -117.9]}
          zoom={8}
          scrollWheelZoom={true}
          zoomControl={false}
          style={{ height: '100%', width: '100%', borderRadius: '0 0 0.75rem 0.75rem' }}
        >
          <TileLayer key={layer} url={TILE_LAYERS[layer].url} attribution={TILE_LAYERS[layer].attribution} />

          {cameras.map(cam => (
            <Marker
              key={cam.code}
              position={[cam.lat, cam.lon]}
              icon={cam.id === selectedCamera ? activeIcon : cameraIcon}
            >
              <Popup>
                <div className="text-sm">
                  <strong>{cam.name}</strong><br />
                  <span className="text-gray-500">{cam.code}</span><br />
                  <span className={cam.online ? 'text-emerald-600' : 'text-red-500'}>
                    {cam.online ? 'Online' : 'Offline'}
                  </span>
                </div>
              </Popup>
            </Marker>
          ))}

          {droneStations.map(ds => {
            const activeDispatch = droneDispatches.find(d => d.stationId === ds.id && d.status !== 'complete')
            return (
              <Marker
                key={ds.id}
                position={[ds.lat, ds.lon]}
                icon={ds.status === 'deployed' ? droneDeployedIcon : droneReadyIcon}
              >
                <Popup>
                  <div className="text-sm min-w-[160px]">
                    <strong>{ds.name}</strong><br />
                    <span className="text-gray-500">{ds.code}</span><br />
                    <span className="text-xs">Drones: {ds.drones} &middot; {ds.payloads.join(', ')}</span><br />
                    <span className={ds.status === 'ready' ? 'text-emerald-600 font-semibold' : 'text-red-500 font-semibold'}>
                      {ds.status === 'ready' ? '● Ready' : '● Deployed'}
                    </span>
                    {activeDispatch && (
                      <><br /><span className="text-xs text-amber-600 font-medium">
                        {activeDispatch.payload} — {activeDispatch.status}
                      </span></>
                    )}
                  </div>
                </Popup>
              </Marker>
            )
          })}

          {hotspots.map((h, i) => (
            <CircleMarker
              key={i}
              center={[h.latitude, h.longitude]}
              radius={10}
              pathOptions={{ color: '#ef4444', fillColor: '#ef4444', fillOpacity: 0.4, weight: 2 }}
            >
              <Popup>
                <div className="text-sm">
                  <strong className="text-red-600">Thermal Hotspot</strong><br />
                  FRP: {h.frp ?? 'N/A'} MW<br />
                  {h.latitude.toFixed(4)}°N, {h.longitude.toFixed(4)}°W
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
    </div>
  )
}
