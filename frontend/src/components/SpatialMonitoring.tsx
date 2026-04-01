import { useState } from 'react'
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet'
import { Icon } from 'leaflet'
import { Map as MapIcon } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'

const CAMERA_LOCATIONS = [
  { name: 'Sierra Peak North', lat: 34.32, lng: -117.73, code: 'cam-01', online: true },
  { name: 'Cajon Pass West', lat: 34.31, lng: -117.45, code: 'cam-02', online: true },
  { name: 'Malibu Canyon', lat: 34.05, lng: -118.68, code: 'cam-03', online: false },
  { name: 'Angeles Crest', lat: 34.25, lng: -118.15, code: 'cam-04', online: false },
]

const cameraIcon = new Icon({
  iconUrl: 'data:image/svg+xml,' + encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" fill="#2563eb" stroke="white" stroke-width="2"/>
      <circle cx="12" cy="12" r="4" fill="white"/>
    </svg>`
  ),
  iconSize: [24, 24],
  iconAnchor: [12, 12],
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
  const dark = theme === 'dark'
  const [layer, setLayer] = useState<LayerOption>('dark')

  return (
    <div
      className={`rounded-xl border overflow-hidden flex flex-col ${
        dark ? 'bg-[#111] border-[#1e1e1e]' : 'bg-white border-gray-200'
      }`}
    >
      <div className={`flex items-center justify-between px-4 py-2.5 border-b ${dark ? 'border-[#1e1e1e]' : 'border-gray-100'}`}>
        <div className="flex items-center gap-2">
          <MapIcon className={`h-3.5 w-3.5 ${dark ? 'text-gray-500' : 'text-gray-400'}`} />
          <span className={`text-xs font-semibold uppercase tracking-wider ${dark ? 'text-gray-400' : 'text-gray-600'}`}>
            Spatial Monitoring
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-[10px] ${dark ? 'text-gray-500' : 'text-gray-400'}`}>Layer</span>
          <select
            value={layer}
            onChange={e => setLayer(e.target.value as LayerOption)}
            className={`text-[10px] rounded-md px-2 py-1 outline-none cursor-pointer ${
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

      <div className="flex-1 min-h-[300px]">
        <MapContainer
          center={[34.2, -117.9]}
          zoom={8}
          scrollWheelZoom={true}
          zoomControl={false}
          style={{ height: '100%', width: '100%', borderRadius: '0 0 0.75rem 0.75rem' }}
        >
          <TileLayer
            key={layer}
            url={TILE_LAYERS[layer].url}
            attribution={TILE_LAYERS[layer].attribution}
          />
          {CAMERA_LOCATIONS.map(cam => (
            <Marker key={cam.code} position={[cam.lat, cam.lng]} icon={cameraIcon}>
              <Popup>
                <div className="text-xs">
                  <strong>{cam.name}</strong>
                  <br />
                  <span className="text-gray-500">{cam.code}</span>
                  <br />
                  <span className={cam.online ? 'text-emerald-600' : 'text-red-500'}>
                    {cam.online ? 'Online' : 'Offline'}
                  </span>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  )
}
