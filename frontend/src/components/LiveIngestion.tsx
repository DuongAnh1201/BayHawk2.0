import { useState, useEffect } from 'react'
import { Video, ShieldCheck, ShieldAlert, Activity, Flame } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import { usePipeline } from '../context/PipelineContext'

const DEMO_VIDEOS: Record<string, { url: string; label: string }> = {
  fire_high: {
    url: 'https://assets.mixkit.co/videos/11028/11028-720.mp4',
    label: 'DEMO — Small Brush Fire',
  },
  critical: {
    url: 'https://assets.mixkit.co/videos/5280/5280-720.mp4',
    label: 'DEMO — Large Wildfire',
  },
}

function alertcaUrl(cam: { lat: number; lon: number; alertcaId?: string }): string {
  const pos = `${cam.lat.toFixed(4)}_${cam.lon.toFixed(4)}_12`
  if (cam.alertcaId) {
    return `https://cameras.alertcalifornia.org/?id=${cam.alertcaId}&pos=${pos}`
  }
  return `https://cameras.alertcalifornia.org/?pos=${pos}`
}

export default function LiveIngestion() {
  const { theme } = useTheme()
  const dark = theme === 'dark' || theme === 'verizon'
  const { cameras, selectedCamera, pipelineResult, isAnalyzing, activeScenario, deescalationPhase } = usePipeline()
  const [fps, setFps] = useState(8.2)

  const cam = cameras.find(c => c.id === selectedCamera)
  const cameraResult = pipelineResult?.camera
  const fusionResult = pipelineResult?.fusion

  const showFireVideo = activeScenario && (!deescalationPhase || deescalationPhase === 'responding' || deescalationPhase === 'containment')
  const demoVideo = showFireVideo ? DEMO_VIDEOS[activeScenario!] : null

  useEffect(() => {
    const interval = setInterval(() => {
      setFps(prev => Math.max(5, Math.min(15, prev + (Math.random() - 0.5) * 1.2)))
    }, 2000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className={`rounded-xl border overflow-hidden flex flex-col h-full ${dark ? 'bg-[#111] border-[#1e1e1e]' : 'bg-white border-gray-200'}`}>
      {/* Header */}
      <div className={`flex items-center justify-between px-4 py-2.5 border-b shrink-0 ${dark ? 'border-[#1e1e1e]' : 'border-gray-100'}`}>
        <div className="flex items-center gap-2">
          <Video className={`h-4 w-4 ${dark ? 'text-gray-500' : 'text-gray-400'}`} />
          <span className={`text-sm font-semibold uppercase tracking-wider ${dark ? 'text-gray-400' : 'text-gray-600'}`}>
            Live Ingestion Engine
          </span>
        </div>
        <div className="flex items-center gap-3">
          {cameraResult && (
            <div className="flex items-center gap-1.5">
              {cameraResult.detected ? (
                <ShieldAlert className="h-4 w-4 text-red-400" />
              ) : (
                <ShieldCheck className="h-4 w-4 text-emerald-400" />
              )}
              <span className={`text-xs font-mono font-bold ${cameraResult.detected ? 'text-red-400' : 'text-emerald-400'}`}>
                YOLO: {(cameraResult.confidence * 100).toFixed(0)}%
              </span>
            </div>
          )}
          <div className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className={`text-xs font-mono ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
              FPS: {fps.toFixed(1)} (Sampled)
            </span>
          </div>
        </div>
      </div>

      {/* Feed area */}
      <div className="relative flex-1 bg-black min-h-0">
        {/* HUD overlays */}
        <div className="absolute top-3 left-3 flex items-center gap-1.5 bg-black/70 backdrop-blur rounded-md px-2.5 py-1.5 z-20">
          <span className={`h-2 w-2 rounded-full ${demoVideo ? 'bg-red-500 animate-pulse' : 'bg-emerald-500'}`} />
          <span className="text-xs font-medium text-white uppercase tracking-wider">
            {cam?.name ?? 'Unknown'}
          </span>
        </div>

        {deescalationPhase ? (
          <div className={`absolute top-3 right-3 flex items-center gap-1.5 backdrop-blur rounded-md px-2.5 py-1.5 z-20 ${
            deescalationPhase === 'extinguished' ? 'bg-emerald-600/80' :
            deescalationPhase === 'controlled' ? 'bg-blue-600/80' :
            deescalationPhase === 'containment' ? 'bg-amber-600/80 animate-pulse' :
            'bg-red-600/80 animate-pulse'
          }`}>
            <Flame className="h-3.5 w-3.5 text-white" />
            <span className="text-xs font-bold text-white uppercase tracking-wider">
              {deescalationPhase === 'extinguished' ? 'FIRE EXTINGUISHED' :
               deescalationPhase === 'controlled' ? 'FIRE CONTROLLED' :
               deescalationPhase === 'containment' ? 'CONTAINMENT IN PROGRESS' :
               'SUPPRESSION UNDERWAY'}
            </span>
          </div>
        ) : demoVideo ? (
          <div className="absolute top-3 right-3 flex items-center gap-1.5 bg-red-600/80 backdrop-blur rounded-md px-2.5 py-1.5 z-20 animate-pulse">
            <Flame className="h-3.5 w-3.5 text-white" />
            <span className="text-xs font-bold text-white uppercase tracking-wider">
              {demoVideo.label}
            </span>
          </div>
        ) : (
          <div className="absolute top-3 right-3 flex items-center gap-1.5 bg-amber-700/70 backdrop-blur rounded-md px-2.5 py-1.5 z-20">
            <span className="text-xs font-medium text-white uppercase tracking-wider">
              AlertCA Live
            </span>
          </div>
        )}

        {cameraResult && (
          <div className={`absolute ${demoVideo ? 'top-12' : 'top-12'} right-3 flex items-center gap-1.5 backdrop-blur rounded-md px-2.5 py-1.5 z-20 ${
            cameraResult.detected ? 'bg-red-500/80' : 'bg-emerald-500/60'
          }`}>
            <Activity className="h-3.5 w-3.5 text-white" />
            <span className="text-xs font-bold text-white uppercase">
              {cameraResult.detected ? 'Fire Detected' : 'Clear'}
            </span>
          </div>
        )}

        {fusionResult && (
          <div className={`absolute bottom-3 left-3 right-3 flex items-center justify-between backdrop-blur rounded-md px-3 py-2 z-20 ${
            fusionResult.status === 'CONFIRMED' ? 'bg-red-900/70' : 'bg-emerald-900/60'
          }`}>
            <span className="text-xs font-bold text-white uppercase tracking-wider">
              Fusion: {fusionResult.status}
            </span>
            <span className="text-xs font-mono text-white/80">
              Combined: {fusionResult.combined_score.toFixed(2)}
            </span>
          </div>
        )}

        {cameraResult?.latency_ms != null && (
          <div className="absolute bottom-14 right-3 z-20">
            <p className="text-[11px] font-mono text-white/50 bg-black/50 rounded px-2 py-1">
              Pipeline: {cameraResult.latency_ms.toFixed(0)}ms
            </p>
          </div>
        )}

        {/* Feed content: demo video, analysis spinner, AlertCA iframe, or placeholder */}
        {isAnalyzing ? (
          <div className="absolute inset-0 flex items-center justify-center z-10">
            <div className="text-center">
              <div className="h-14 w-14 border-2 border-brand border-t-transparent rounded-full animate-spin mx-auto mb-3" />
              <p className="text-sm text-gray-400 font-mono">Running pipeline analysis...</p>
            </div>
          </div>
        ) : demoVideo ? (
          <video
            key={demoVideo.url}
            src={demoVideo.url}
            className="absolute inset-0 w-full h-full object-cover"
            autoPlay
            loop
            muted
            playsInline
          />
        ) : cam ? (
          <iframe
            key={cam.id}
            src={alertcaUrl(cam)}
            title={`AlertCA — ${cam.name}`}
            className="absolute inset-0 w-full h-full border-0"
            allow="autoplay"
            referrerPolicy="no-referrer"
          />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="text-sm text-gray-500 font-mono">No camera selected</p>
          </div>
        )}
      </div>
    </div>
  )
}
