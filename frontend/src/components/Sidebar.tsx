import { useState } from 'react'
import { Radio, RefreshCw } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'

interface CameraNode {
  id: string
  name: string
  code: string
  online: boolean
}

const CAMERAS: CameraNode[] = [
  { id: '1', name: 'Sierra Peak North', code: 'cam-01', online: true },
  { id: '2', name: 'Cajon Pass West', code: 'cam-02', online: true },
  { id: '3', name: 'Malibu Canyon', code: 'cam-03', online: false },
  { id: '4', name: 'Angeles Crest', code: 'cam-04', online: false },
]

export default function Sidebar() {
  const { theme } = useTheme()
  const dark = theme === 'dark'
  const [selected, setSelected] = useState('1')

  return (
    <aside
      className={`w-[220px] shrink-0 flex flex-col border-r overflow-y-auto ${
        dark ? 'bg-[#0a0a0a] border-[#1e1e1e]' : 'bg-gray-50 border-gray-200'
      }`}
    >
      {/* Camera Nodes */}
      <div className="p-4">
        <div className="flex items-center justify-between mb-3">
          <span className={`text-[10px] font-semibold uppercase tracking-wider ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
            Camera Nodes
          </span>
          <span
            className={`text-[10px] font-medium rounded-full px-1.5 py-0.5 ${
              dark ? 'bg-[#1a1a1a] text-gray-400' : 'bg-gray-200 text-gray-500'
            }`}
          >
            {CAMERAS.length}
          </span>
        </div>

        <div className="flex flex-col gap-1.5">
          {CAMERAS.map(cam => (
            <button
              key={cam.id}
              onClick={() => setSelected(cam.id)}
              className={`w-full flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-left transition-colors cursor-pointer ${
                selected === cam.id
                  ? dark
                    ? 'bg-brand/15 border border-brand/30'
                    : 'bg-amber-50 border border-amber-200'
                  : dark
                    ? 'hover:bg-[#141414] border border-transparent'
                    : 'hover:bg-gray-100 border border-transparent'
              }`}
            >
              <Radio
                className={`h-3.5 w-3.5 shrink-0 ${
                  selected === cam.id ? 'text-brand' : dark ? 'text-gray-600' : 'text-gray-400'
                }`}
              />
              <div className="min-w-0 flex-1">
                <p
                  className={`text-xs font-medium truncate ${
                    selected === cam.id
                      ? dark ? 'text-white' : 'text-gray-900'
                      : dark ? 'text-gray-300' : 'text-gray-700'
                  }`}
                >
                  {cam.name}
                </p>
                <p className={`text-[10px] ${dark ? 'text-gray-600' : 'text-gray-400'}`}>
                  {cam.code}
                </p>
              </div>
              <span
                className={`h-2 w-2 rounded-full shrink-0 ${
                  cam.online ? 'bg-emerald-500' : 'bg-gray-500'
                }`}
              />
            </button>
          ))}
        </div>
      </div>

      {/* Recent Alerts */}
      <div className={`p-4 border-t ${dark ? 'border-[#1e1e1e]' : 'border-gray-200'}`}>
        <div className="flex items-center justify-between mb-4">
          <span className={`text-[10px] font-semibold uppercase tracking-wider ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
            Recent Alerts
          </span>
          <RefreshCw className={`h-3 w-3 ${dark ? 'text-gray-600' : 'text-gray-400'}`} />
        </div>

        <div className="flex flex-col items-center justify-center py-6">
          <div
            className={`h-12 w-12 rounded-full flex items-center justify-center mb-3 ${
              dark ? 'bg-[#141414]' : 'bg-gray-100'
            }`}
          >
            <RefreshCw className={`h-5 w-5 ${dark ? 'text-gray-600' : 'text-gray-400'}`} />
          </div>
          <p className={`text-[10px] font-medium uppercase tracking-wider ${dark ? 'text-gray-600' : 'text-gray-400'}`}>
            No Active Threats
          </p>
        </div>
      </div>
    </aside>
  )
}
