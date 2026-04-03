import { useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet'
import { Icon, DivIcon } from 'leaflet'
import {
  Crosshair, Rocket, RotateCcw, CheckCircle, Navigation,
  Droplets, Wind, Package, Battery, Gauge,
} from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import { usePipeline, type DroneStation, type DroneDispatch } from '../context/PipelineContext'

const STATUS_LABELS: Record<string, { label: string; color: string; icon: typeof Rocket }> = {
  launching: { label: 'Launching', color: 'text-amber-400', icon: Rocket },
  'en-route': { label: 'En Route', color: 'text-blue-400', icon: Navigation },
  dropping: { label: 'Dropping Payload', color: 'text-red-400', icon: Droplets },
  returning: { label: 'Returning', color: 'text-purple-400', icon: Wind },
  complete: { label: 'Complete', color: 'text-emerald-400', icon: CheckCircle },
}

const PAYLOAD_COLORS: Record<string, string> = {
  'Water Bomb': 'text-blue-400 bg-blue-400/10',
  'Smoke Bomb': 'text-gray-300 bg-gray-400/10',
  'Retardant': 'text-red-400 bg-red-400/10',
}

function makeStationIcon(status: 'ready' | 'deployed', dronesAvailable: number, total: number) {
  const fill = status === 'deployed' ? '#dc2626' : '#059669'
  const pct = total > 0 ? Math.round((dronesAvailable / total) * 100) : 0
  return new Icon({
    iconUrl:
      'data:image/svg+xml,' +
      encodeURIComponent(
        `<svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 36 36">
          <rect x="2" y="2" width="32" height="32" rx="8" fill="${fill}" stroke="white" stroke-width="2"/>
          <text x="18" y="15" text-anchor="middle" fill="white" font-size="9" font-weight="bold" font-family="sans-serif">${dronesAvailable}/${total}</text>
          <text x="18" y="26" text-anchor="middle" fill="white" font-size="7" font-family="sans-serif">${pct}%</text>
        </svg>`,
      ),
    iconSize: [36, 36],
    iconAnchor: [18, 18],
  })
}

const cameraIcon = new Icon({
  iconUrl:
    'data:image/svg+xml,' +
    encodeURIComponent(
      `<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 20 20">
        <circle cx="10" cy="10" r="8" fill="#2563eb" stroke="white" stroke-width="1.5" opacity="0.6"/>
        <circle cx="10" cy="10" r="3" fill="white" opacity="0.8"/>
      </svg>`,
    ),
  iconSize: [20, 20],
  iconAnchor: [10, 10],
})

function makeDroneIcon(status: string) {
  const color = status === 'launching' ? '#f59e0b'
    : status === 'en-route' ? '#3b82f6'
    : status === 'dropping' ? '#ef4444'
    : status === 'returning' ? '#a855f7'
    : '#10b981'
  return new DivIcon({
    html: `<div style="width:20px;height:20px;background:${color};border:2px solid white;border-radius:50%;box-shadow:0 0 8px ${color};animation:pulse 1s infinite"></div>`,
    iconSize: [20, 20],
    iconAnchor: [10, 10],
    className: '',
  })
}

function interpolatePos(
  from: [number, number],
  to: [number, number],
  status: DroneDispatch['status'],
): [number, number] {
  const progress =
    status === 'launching' ? 0.05
    : status === 'en-route' ? 0.5
    : status === 'dropping' ? 0.95
    : status === 'returning' ? 0.4
    : 0
  return [
    from[0] + (to[0] - from[0]) * progress,
    from[1] + (to[1] - from[1]) * progress,
  ]
}

type ActiveTab = 'overview' | 'inventory' | 'deploy'

export default function DroneSystemPanel() {
  const { theme } = useTheme()
  const dark = theme === 'dark' || theme === 'verizon'
  const {
    cameras,
    droneStations,
    droneDispatches,
    nearestStation,
    dispatchDrone,
    resetDrones,
    selectedCamera,
  } = usePipeline()

  const [activeTab, setActiveTab] = useState<ActiveTab>('overview')
  const [selectedPayload, setSelectedPayload] = useState('Water Bomb')
  const [selectedStation, setSelectedStation] = useState<string | null>(null)

  const station: DroneStation | null = selectedStation
    ? droneStations.find(s => s.id === selectedStation) ?? null
    : nearestStation

  const activeDispatches = droneDispatches.filter(d => d.status !== 'complete')
  const completedDispatches = droneDispatches.filter(d => d.status === 'complete')
  const totalDrones = droneStations.reduce((a, s) => a + s.dronesTotal, 0)
  const availDrones = droneStations.reduce((a, s) => a + s.drones, 0)
  const totalStock = droneStations.reduce((a, s) => a + s.stock.reduce((b, st) => b + st.available, 0), 0)
  const totalStockMax = droneStations.reduce((a, s) => a + s.stock.reduce((b, st) => b + st.total, 0), 0)

  const cam = cameras.find(c => c.id === selectedCamera)
  const targetPos: [number, number] = cam ? [cam.lat, cam.lon] : [34.2, -117.9]

  const TABS: { key: ActiveTab; label: string }[] = [
    { key: 'overview', label: 'Overview' },
    { key: 'inventory', label: 'Inventory' },
    { key: 'deploy', label: 'Deploy' },
  ]

  return (
    <div className={`flex flex-col h-full rounded-xl border overflow-hidden ${dark ? 'bg-[#0a0a0a] border-[#1e1e1e]' : 'bg-white border-gray-200'}`}>
      {/* Header */}
      <div className={`flex items-center justify-between px-4 py-2.5 border-b shrink-0 ${dark ? 'border-[#1e1e1e]' : 'border-gray-100'}`}>
        <div className="flex items-center gap-2">
          <Crosshair className="h-4 w-4 text-emerald-400" />
          <span className={`text-sm font-semibold uppercase tracking-wider ${dark ? 'text-gray-400' : 'text-gray-600'}`}>
            Drone Command System
          </span>
          {activeDispatches.length > 0 && (
            <span className="text-xs font-bold text-amber-400 bg-amber-400/10 rounded px-2 py-0.5 animate-pulse">
              {activeDispatches.length} active
            </span>
          )}
        </div>
        <button
          onClick={resetDrones}
          className={`text-xs flex items-center gap-1 px-2 py-1 rounded cursor-pointer transition-colors ${dark ? 'text-gray-500 hover:text-white hover:bg-[#1a1a1a]' : 'text-gray-400 hover:text-gray-700 hover:bg-gray-100'}`}
        >
          <RotateCcw className="h-3 w-3" /> Reset All
        </button>
      </div>

      {/* Fleet summary strip */}
      <div className={`grid grid-cols-4 gap-px shrink-0 ${dark ? 'bg-[#1e1e1e]' : 'bg-gray-200'}`}>
        {[
          { label: 'Stations', value: droneStations.length, icon: Crosshair, color: 'text-emerald-400' },
          { label: 'Drones', value: `${availDrones}/${totalDrones}`, icon: Gauge, color: 'text-blue-400' },
          { label: 'Active', value: activeDispatches.length, icon: Navigation, color: activeDispatches.length > 0 ? 'text-amber-400' : 'text-gray-500' },
          { label: 'Payload Stock', value: `${totalStock}/${totalStockMax}`, icon: Package, color: totalStock < totalStockMax * 0.3 ? 'text-red-400' : 'text-emerald-400' },
        ].map(s => (
          <div key={s.label} className={`flex items-center gap-2 px-3 py-2 ${dark ? 'bg-[#0e0e0e]' : 'bg-gray-50'}`}>
            <s.icon className={`h-3.5 w-3.5 ${s.color}`} />
            <div>
              <p className={`text-[11px] uppercase tracking-wider ${dark ? 'text-gray-600' : 'text-gray-400'}`}>{s.label}</p>
              <p className={`text-sm font-bold ${dark ? 'text-white' : 'text-gray-900'}`}>{s.value}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Tab bar */}
      <div className={`flex items-center gap-1 px-3 py-1.5 border-b shrink-0 ${dark ? 'border-[#1e1e1e]' : 'border-gray-100'}`}>
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-colors cursor-pointer ${
              activeTab === tab.key
                ? 'bg-brand text-white'
                : dark ? 'text-gray-500 hover:text-white hover:bg-[#1a1a1a]' : 'text-gray-500 hover:text-gray-900 hover:bg-gray-100'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Content area */}
      <div className="flex-1 min-h-0 flex flex-col">
        {activeTab === 'overview' && (
          <div className="flex-1 flex min-h-0">
            {/* Map — left side */}
            <div className="flex-1 min-h-0 relative">
              <MapContainer
                center={[34.22, -118.0]}
                zoom={9}
                scrollWheelZoom={true}
                zoomControl={false}
                style={{ height: '100%', width: '100%' }}
              >
                <TileLayer
                  url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>'
                />

                {/* Cameras (dimmed) */}
                {cameras.map(c => (
                  <Marker key={c.code} position={[c.lat, c.lon]} icon={cameraIcon}>
                    <Popup><div className="text-xs"><strong>{c.name}</strong><br />{c.code}</div></Popup>
                  </Marker>
                ))}

                {/* Drone stations */}
                {droneStations.map(ds => (
                  <Marker
                    key={ds.id}
                    position={[ds.lat, ds.lon]}
                    icon={makeStationIcon(ds.status, ds.drones, ds.dronesTotal)}
                  >
                    <Popup>
                      <div className="text-sm min-w-[180px]">
                        <strong>{ds.name}</strong>
                        <span className="text-gray-500 ml-1">({ds.code})</span>
                        <hr className="my-1" />
                        <p className="text-xs">Drones: <strong>{ds.drones}/{ds.dronesTotal}</strong></p>
                        {ds.stock.map(st => (
                          <p key={st.type} className="text-xs">{st.type}: <strong>{st.available}/{st.total}</strong></p>
                        ))}
                        <p className={`text-xs font-semibold mt-1 ${ds.status === 'ready' ? 'text-emerald-600' : 'text-red-500'}`}>
                          {ds.status === 'ready' ? '● Ready' : '● Deployed'}
                        </p>
                      </div>
                    </Popup>
                  </Marker>
                ))}

                {/* Active drone flight paths */}
                {activeDispatches.map((d, i) => {
                  const stationData = droneStations.find(s => s.id === d.stationId)
                  if (!stationData) return null
                  const from: [number, number] = [stationData.lat, stationData.lon]
                  const dronePos = interpolatePos(from, targetPos, d.status)
                  return (
                    <span key={i}>
                      <Polyline
                        positions={[from, dronePos]}
                        pathOptions={{
                          color: d.status === 'dropping' ? '#ef4444' : d.status === 'returning' ? '#a855f7' : '#3b82f6',
                          weight: 2,
                          dashArray: '6 4',
                          opacity: 0.7,
                        }}
                      />
                      <Marker position={dronePos} icon={makeDroneIcon(d.status)}>
                        <Popup>
                          <div className="text-xs">
                            <strong>Drone — {d.payload}</strong><br />
                            From: {stationData.name}<br />
                            Status: <strong>{STATUS_LABELS[d.status]?.label ?? d.status}</strong>
                          </div>
                        </Popup>
                      </Marker>
                    </span>
                  )
                })}
              </MapContainer>
            </div>

            {/* Mission tracker — right side */}
            <div className={`w-[280px] shrink-0 border-l overflow-y-auto ${dark ? 'border-[#1e1e1e]' : 'border-gray-200'}`}>
              <div className="p-3">
                <p className={`text-[11px] font-semibold uppercase tracking-wider mb-2 ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
                  Active Missions ({activeDispatches.length})
                </p>

                {activeDispatches.length === 0 && (
                  <div className="flex flex-col items-center justify-center py-8">
                    <Battery className={`h-8 w-8 mb-2 ${dark ? 'text-gray-700' : 'text-gray-300'}`} />
                    <p className={`text-xs ${dark ? 'text-gray-600' : 'text-gray-400'}`}>No active missions</p>
                  </div>
                )}

                <div className="flex flex-col gap-2">
                  {activeDispatches.map((d, i) => {
                    const info = STATUS_LABELS[d.status]
                    const stationData = droneStations.find(s => s.id === d.stationId)
                    const StatusIcon = info?.icon ?? Rocket
                    const elapsed = Math.round((Date.now() - d.startedAt) / 1000)
                    return (
                      <div key={i} className={`rounded-lg p-3 border ${dark ? 'bg-[#141414] border-[#2a2a2a]' : 'bg-gray-50 border-gray-200'}`}>
                        <div className="flex items-center justify-between mb-1.5">
                          <div className="flex items-center gap-1.5">
                            <StatusIcon className={`h-4 w-4 ${info?.color ?? 'text-gray-400'} animate-pulse`} />
                            <span className={`text-xs font-bold ${info?.color ?? 'text-gray-400'}`}>
                              {info?.label ?? d.status}
                            </span>
                          </div>
                          <span className={`text-[11px] font-mono ${dark ? 'text-gray-600' : 'text-gray-400'}`}>
                            {elapsed}s ago
                          </span>
                        </div>
                        <p className={`text-xs font-medium ${dark ? 'text-gray-300' : 'text-gray-700'}`}>
                          {stationData?.name ?? d.stationId}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className={`text-[11px] px-1.5 py-0.5 rounded ${PAYLOAD_COLORS[d.payload] ?? 'text-gray-400 bg-gray-400/10'}`}>
                            {d.payload}
                          </span>
                        </div>
                        {/* Progress bar */}
                        <div className={`mt-2 h-1.5 rounded-full overflow-hidden ${dark ? 'bg-[#2a2a2a]' : 'bg-gray-200'}`}>
                          <div
                            className={`h-full rounded-full transition-all duration-1000 ${
                              d.status === 'launching' ? 'bg-amber-400 w-[15%]'
                              : d.status === 'en-route' ? 'bg-blue-400 w-[40%]'
                              : d.status === 'dropping' ? 'bg-red-400 w-[70%]'
                              : d.status === 'returning' ? 'bg-purple-400 w-[90%]'
                              : 'bg-emerald-400 w-full'
                            }`}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>

                {completedDispatches.length > 0 && (
                  <div className={`mt-3 pt-3 border-t ${dark ? 'border-[#1e1e1e]' : 'border-gray-100'}`}>
                    <p className={`text-[11px] font-semibold uppercase tracking-wider mb-2 ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
                      Completed ({completedDispatches.length})
                    </p>
                    {completedDispatches.map((d, i) => {
                      const stationData = droneStations.find(s => s.id === d.stationId)
                      return (
                        <div key={i} className={`flex items-center gap-2 py-1.5 ${dark ? 'text-gray-600' : 'text-gray-400'}`}>
                          <CheckCircle className="h-3 w-3 text-emerald-500 shrink-0" />
                          <span className="text-[11px] truncate">{stationData?.name} — {d.payload}</span>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'inventory' && (
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {droneStations.map(ds => {
              const dronePercent = ds.dronesTotal > 0 ? Math.round((ds.drones / ds.dronesTotal) * 100) : 0
              return (
                <div key={ds.id} className={`rounded-xl border ${dark ? 'bg-[#111] border-[#1e1e1e]' : 'bg-gray-50 border-gray-200'}`}>
                  {/* Station header */}
                  <div className={`flex items-center justify-between px-4 py-3 border-b ${dark ? 'border-[#1e1e1e]' : 'border-gray-200'}`}>
                    <div className="flex items-center gap-3">
                      <div className={`h-10 w-10 rounded-lg flex items-center justify-center ${
                        ds.status === 'ready' ? 'bg-emerald-500/15' : 'bg-red-500/15'
                      }`}>
                        <Crosshair className={`h-5 w-5 ${ds.status === 'ready' ? 'text-emerald-400' : 'text-red-400'}`} />
                      </div>
                      <div>
                        <p className={`text-sm font-bold ${dark ? 'text-white' : 'text-gray-900'}`}>{ds.name}</p>
                        <p className={`text-xs ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
                          {ds.code} &middot; {ds.lat.toFixed(3)}°N, {Math.abs(ds.lon).toFixed(3)}°W
                        </p>
                      </div>
                    </div>
                    <span className={`text-xs font-bold px-2.5 py-1 rounded-lg ${
                      ds.status === 'ready' ? 'text-emerald-400 bg-emerald-400/10' : 'text-red-400 bg-red-400/10'
                    }`}>
                      {ds.status === 'ready' ? 'OPERATIONAL' : 'DEPLOYED'}
                    </span>
                  </div>

                  <div className="p-4 space-y-3">
                    {/* Drone fleet */}
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className={`text-[11px] font-semibold uppercase tracking-wider ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
                          Drone Fleet
                        </span>
                        <span className={`text-xs font-bold ${dark ? 'text-white' : 'text-gray-900'}`}>
                          {ds.drones}/{ds.dronesTotal} available
                        </span>
                      </div>
                      <div className={`h-2.5 rounded-full overflow-hidden ${dark ? 'bg-[#1e1e1e]' : 'bg-gray-200'}`}>
                        <div
                          className={`h-full rounded-full transition-all ${
                            dronePercent > 60 ? 'bg-emerald-500' : dronePercent > 30 ? 'bg-amber-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${dronePercent}%` }}
                        />
                      </div>
                      {/* Individual drone indicators */}
                      <div className="flex items-center gap-1.5 mt-2">
                        {Array.from({ length: ds.dronesTotal }).map((_, i) => (
                          <div
                            key={i}
                            className={`h-6 w-6 rounded flex items-center justify-center text-[10px] font-bold ${
                              i < ds.drones
                                ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                                : 'bg-red-500/15 text-red-400 border border-red-500/30'
                            }`}
                          >
                            {i < ds.drones ? '✓' : '→'}
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Payload stock */}
                    <div>
                      <span className={`text-[11px] font-semibold uppercase tracking-wider block mb-2 ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
                        Payload Stock
                      </span>
                      <div className="grid grid-cols-3 gap-2">
                        {ds.stock.map(st => {
                          const pct = st.total > 0 ? Math.round((st.available / st.total) * 100) : 0
                          return (
                            <div key={st.type} className={`rounded-lg p-2.5 border ${dark ? 'bg-[#0e0e0e] border-[#1e1e1e]' : 'bg-white border-gray-200'}`}>
                              <div className="flex items-center gap-1.5 mb-1.5">
                                <Package className={`h-3 w-3 ${PAYLOAD_COLORS[st.type]?.split(' ')[0] ?? 'text-gray-400'}`} />
                                <span className={`text-[11px] font-medium ${dark ? 'text-gray-400' : 'text-gray-600'}`}>{st.type}</span>
                              </div>
                              <p className={`text-lg font-bold ${dark ? 'text-white' : 'text-gray-900'}`}>
                                {st.available}<span className={`text-xs font-normal ${dark ? 'text-gray-600' : 'text-gray-400'}`}>/{st.total}</span>
                              </p>
                              <div className={`mt-1.5 h-1.5 rounded-full overflow-hidden ${dark ? 'bg-[#1e1e1e]' : 'bg-gray-200'}`}>
                                <div
                                  className={`h-full rounded-full ${pct > 50 ? 'bg-emerald-500' : pct > 20 ? 'bg-amber-500' : 'bg-red-500'}`}
                                  style={{ width: `${pct}%` }}
                                />
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {activeTab === 'deploy' && (
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {/* Station selector */}
            <div>
              <label className={`text-[11px] font-semibold uppercase tracking-wider block mb-2 ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
                Select Station {station && nearestStation?.id === station.id && <span className="text-emerald-400 normal-case">(nearest to camera)</span>}
              </label>
              <div className="grid grid-cols-3 gap-2">
                {droneStations.map(ds => (
                  <button
                    key={ds.id}
                    onClick={() => setSelectedStation(ds.id)}
                    className={`rounded-lg p-3 text-left transition-all cursor-pointer border ${
                      (selectedStation ?? nearestStation?.id) === ds.id
                        ? dark ? 'bg-emerald-500/10 border-emerald-500/30 ring-1 ring-emerald-500/20' : 'bg-emerald-50 border-emerald-300 ring-1 ring-emerald-200'
                        : dark ? 'bg-[#141414] border-[#1e1e1e] hover:border-[#2a2a2a]' : 'bg-gray-50 border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <p className={`text-xs font-bold ${dark ? 'text-white' : 'text-gray-900'}`}>{ds.name}</p>
                    <p className={`text-[11px] mt-0.5 ${dark ? 'text-gray-600' : 'text-gray-400'}`}>
                      {ds.code} &middot; {ds.drones} drone{ds.drones !== 1 ? 's' : ''}
                    </p>
                    <div className="flex items-center gap-1.5 mt-1.5">
                      {ds.stock.map(st => (
                        <span key={st.type} className={`text-[10px] px-1.5 py-0.5 rounded ${PAYLOAD_COLORS[st.type] ?? 'text-gray-400 bg-gray-400/10'}`}>
                          {st.available}× {st.type.replace(' Bomb', '')}
                        </span>
                      ))}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Payload + deploy */}
            {station && (
              <>
                <div>
                  <label className={`text-[11px] font-semibold uppercase tracking-wider block mb-2 ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
                    Select Payload
                  </label>
                  <div className="flex gap-2 flex-wrap">
                    {station.stock.map(st => {
                      const outOfStock = st.available === 0
                      return (
                        <button
                          key={st.type}
                          onClick={() => !outOfStock && setSelectedPayload(st.type)}
                          disabled={outOfStock}
                          className={`px-4 py-2.5 rounded-lg text-xs font-medium cursor-pointer transition-all border ${
                            outOfStock
                              ? 'opacity-30 cursor-not-allowed border-transparent bg-gray-500/10 text-gray-500'
                              : selectedPayload === st.type
                                ? 'bg-brand text-white border-brand'
                                : dark ? 'bg-[#1a1a1a] text-gray-400 hover:text-white border-transparent' : 'bg-gray-100 text-gray-600 hover:text-gray-900 border-transparent'
                          }`}
                        >
                          {st.type} ({st.available})
                        </button>
                      )
                    })}
                  </div>
                </div>

                <button
                  onClick={() => station.drones > 0 && dispatchDrone(station.id, selectedPayload)}
                  disabled={station.drones === 0}
                  className="w-full flex items-center justify-center gap-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 disabled:opacity-40 disabled:cursor-not-allowed px-4 py-3 text-sm font-bold uppercase tracking-wider text-white transition-colors cursor-pointer"
                >
                  <Rocket className="h-5 w-5" />
                  Deploy Drone — {selectedPayload}
                </button>

                {station.drones === 0 && (
                  <p className="text-center text-xs text-red-400 bg-red-400/10 rounded-lg py-2">
                    All drones deployed from this station
                  </p>
                )}
              </>
            )}

            {/* Quick mission list */}
            {activeDispatches.length > 0 && (
              <div>
                <p className={`text-[11px] font-semibold uppercase tracking-wider mb-2 ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
                  Active Missions
                </p>
                <div className="flex flex-col gap-1.5">
                  {activeDispatches.map((d, i) => {
                    const info = STATUS_LABELS[d.status]
                    const stationData = droneStations.find(s => s.id === d.stationId)
                    const StatusIcon = info?.icon ?? Rocket
                    return (
                      <div key={i} className={`flex items-center justify-between rounded-lg px-3 py-2 border ${dark ? 'bg-[#141414] border-[#2a2a2a]' : 'bg-gray-50 border-gray-200'}`}>
                        <div className="flex items-center gap-2">
                          <StatusIcon className={`h-3.5 w-3.5 ${info?.color ?? 'text-gray-400'} animate-pulse`} />
                          <span className={`text-xs ${dark ? 'text-gray-300' : 'text-gray-700'}`}>{stationData?.name}</span>
                          <span className={`text-[10px] px-1.5 py-0.5 rounded ${PAYLOAD_COLORS[d.payload] ?? 'text-gray-400 bg-gray-400/10'}`}>{d.payload}</span>
                        </div>
                        <span className={`text-[11px] font-semibold ${info?.color ?? 'text-gray-400'}`}>{info?.label}</span>
                      </div>
                    )
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
