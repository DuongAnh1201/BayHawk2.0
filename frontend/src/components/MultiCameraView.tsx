import { Maximize2, Video } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import { usePipeline } from '../context/PipelineContext'
import type { CameraNode } from '../types/pipeline'

function alertcaUrl(cam: CameraNode): string {
  const pos = `${cam.lat.toFixed(4)}_${cam.lon.toFixed(4)}_12`
  if (cam.alertcaId) {
    return `https://cameras.alertcalifornia.org/?id=${cam.alertcaId}&pos=${pos}`
  }
  return `https://cameras.alertcalifornia.org/?pos=${pos}`
}

interface Props {
  onFocusCamera: (id: string) => void
}

export default function MultiCameraView({ onFocusCamera }: Props) {
  const { theme } = useTheme()
  const dark = theme === 'dark' || theme === 'verizon'
  const { cameras, selectedCamera, pipelineResult } = usePipeline()

  const fusionStatus = pipelineResult?.fusion?.status
  const cameraDetected = pipelineResult?.camera?.detected

  return (
    <div className="grid grid-cols-2 gap-3 h-full">
      {cameras.map(cam => {
        const isActive = cam.id === selectedCamera
        const showAlert = isActive && cameraDetected

        return (
          <div
            key={cam.id}
            className={`rounded-xl border overflow-hidden flex flex-col relative group ${
              dark ? 'bg-[#111] border-[#1e1e1e]' : 'bg-white border-gray-200'
            } ${isActive ? (dark ? 'ring-2 ring-brand/50' : 'ring-2 ring-amber-400/50') : ''}`}
          >
            {/* Camera header */}
            <div className={`flex items-center justify-between px-3 py-2 border-b shrink-0 ${dark ? 'border-[#1e1e1e]' : 'border-gray-100'}`}>
              <div className="flex items-center gap-2">
                <Video className={`h-3.5 w-3.5 ${dark ? 'text-gray-500' : 'text-gray-400'}`} />
                <span className={`text-xs font-semibold uppercase tracking-wider ${dark ? 'text-gray-400' : 'text-gray-600'}`}>
                  {cam.name}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`text-[11px] font-mono ${dark ? 'text-gray-600' : 'text-gray-400'}`}>
                  {cam.code}
                </span>
                <span className={`h-2 w-2 rounded-full shrink-0 ${cam.online ? 'bg-emerald-500' : 'bg-gray-500'}`} />
              </div>
            </div>

            {/* Feed */}
            <div className="relative flex-1 bg-black min-h-0">
              <iframe
                src={alertcaUrl(cam)}
                title={`AlertCA — ${cam.name}`}
                className="absolute inset-0 w-full h-full border-0"
                allow="autoplay"
                referrerPolicy="no-referrer"
              />

              {/* Status badge */}
              {showAlert && (
                <div className={`absolute top-2 left-2 z-20 flex items-center gap-1.5 backdrop-blur rounded-md px-2 py-1 ${
                  fusionStatus === 'CONFIRMED' ? 'bg-red-500/80' : 'bg-emerald-500/60'
                }`}>
                  <span className="text-[11px] font-bold text-white uppercase">
                    {fusionStatus === 'CONFIRMED' ? 'ALERT' : 'Clear'}
                  </span>
                </div>
              )}

              {/* AlertCA badge */}
              <div className="absolute top-2 right-2 z-20 bg-amber-700/70 backdrop-blur rounded-md px-2 py-1">
                <span className="text-[11px] font-medium text-white uppercase tracking-wider">
                  AlertCA
                </span>
              </div>

              {/* Focus button — appears on hover */}
              <button
                onClick={() => onFocusCamera(cam.id)}
                className="absolute bottom-2 right-2 z-20 flex items-center gap-1.5 bg-brand/90 hover:bg-brand backdrop-blur rounded-md px-3 py-1.5 text-white opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
              >
                <Maximize2 className="h-3.5 w-3.5" />
                <span className="text-xs font-semibold uppercase tracking-wider">Focus</span>
              </button>
            </div>
          </div>
        )
      })}
    </div>
  )
}
