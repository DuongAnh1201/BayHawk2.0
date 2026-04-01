import { useState, useEffect } from 'react'
import { Video } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'

export default function LiveIngestion() {
  const { theme } = useTheme()
  const dark = theme === 'dark'
  const [fps, setFps] = useState(8.2)

  useEffect(() => {
    const interval = setInterval(() => {
      setFps(prev => {
        const jitter = (Math.random() - 0.5) * 1.2
        return Math.max(5, Math.min(15, prev + jitter))
      })
    }, 2000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div
      className={`rounded-xl border overflow-hidden flex flex-col ${
        dark ? 'bg-[#111] border-[#1e1e1e]' : 'bg-white border-gray-200'
      }`}
    >
      {/* Header */}
      <div className={`flex items-center justify-between px-4 py-2.5 border-b ${dark ? 'border-[#1e1e1e]' : 'border-gray-100'}`}>
        <div className="flex items-center gap-2">
          <Video className={`h-3.5 w-3.5 ${dark ? 'text-gray-500' : 'text-gray-400'}`} />
          <span className={`text-xs font-semibold uppercase tracking-wider ${dark ? 'text-gray-400' : 'text-gray-600'}`}>
            Live Ingestion Engine
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className={`text-[10px] font-mono ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
            FPS: {fps.toFixed(1)} (Sampled)
          </span>
        </div>
      </div>

      {/* Video area */}
      <div className="relative flex-1 min-h-[240px] bg-black flex items-center justify-center">
        <div className="absolute top-3 left-3 flex items-center gap-1.5 bg-black/70 backdrop-blur rounded-md px-2.5 py-1">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
          <span className="text-[10px] font-medium text-white uppercase tracking-wider">
            Sierra Peak North
          </span>
        </div>

        {/* Placeholder feed visualization */}
        <div className="text-center">
          <div className="relative w-48 h-32 mx-auto mb-3 rounded-lg overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-emerald-900/30 via-transparent to-amber-900/20" />
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-16 h-16 border-2 border-brand/50 rounded-lg flex items-center justify-center">
                <Video className="h-6 w-6 text-brand/70" />
              </div>
            </div>
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-brand/30">
              <div className="h-full bg-brand animate-pulse" style={{ width: '60%' }} />
            </div>
          </div>
          <p className="text-[10px] text-gray-500 font-mono">RTSP STREAM ACTIVE</p>
        </div>

        {/* Scan lines overlay */}
        <div
          className="absolute inset-0 pointer-events-none opacity-5"
          style={{
            backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.03) 2px, rgba(255,255,255,0.03) 4px)',
          }}
        />
      </div>
    </div>
  )
}
