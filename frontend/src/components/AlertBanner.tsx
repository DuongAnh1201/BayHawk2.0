import { useState, useEffect, useRef } from 'react'
import {
  AlertTriangle, X, MessageSquare, Volume2, VolumeX,
  CheckCircle, Users, Radio, MapPin, Siren,
} from 'lucide-react'
import { usePipeline } from '../context/PipelineContext'
import { sendSMSAlert } from '../services/sms'
import SMSPanel from './SMSPanel'

const CRITICALITY_THRESHOLD = ['HIGH', 'CRITICAL'] as const

export default function AlertBanner() {
  const { pipelineResult, cameras, selectedCamera } = usePipeline()
  const [dismissed, setDismissed] = useState(false)
  const [smsOpen, setSmsOpen] = useState(false)
  const [audioEnabled, setAudioEnabled] = useState(true)
  const prevEventId = useRef<string | null>(null)
  const audioCtxRef = useRef<AudioContext | null>(null)
  const autoSentRef = useRef<string | null>(null)

  const [autoSmsStatus, setAutoSmsStatus] = useState<'idle' | 'sending' | 'sent'>('idle')

  const fusion = pipelineResult?.fusion
  const classification = pipelineResult?.classification
  const suggestion = pipelineResult?.suggestion
  const cam = cameras.find(c => c.id === selectedCamera)

  const isActive =
    fusion?.status === 'CONFIRMED' &&
    classification &&
    CRITICALITY_THRESHOLD.includes(classification.criticality as 'HIGH' | 'CRITICAL')

  const isCritical = isActive && classification?.criticality === 'CRITICAL'

  const alertMessage = suggestion?.alert_message
    ?? `WILDFIRE ALERT — ${classification?.criticality ?? 'UNKNOWN'} criticality detected at ${cam?.name ?? 'Unknown location'}.`

  useEffect(() => {
    if (pipelineResult?.event_id && pipelineResult.event_id !== prevEventId.current) {
      prevEventId.current = pipelineResult.event_id
      setDismissed(false)
      setAutoSmsStatus('idle')
    }
  }, [pipelineResult?.event_id])

  // Auto-send SMS to firefighters + control center on CRITICAL
  useEffect(() => {
    if (!isCritical || dismissed) return
    if (autoSentRef.current === pipelineResult?.event_id) return

    autoSentRef.current = pipelineResult?.event_id ?? null
    setAutoSmsStatus('sending')

    sendSMSAlert({
      groups: ['firefighters', 'control_center'],
      message: alertMessage,
      camera_name: cam?.name ?? 'Unknown',
      criticality: 'CRITICAL',
      lat: cam?.lat,
      lon: cam?.lon,
    }).then(() => {
      setAutoSmsStatus('sent')
    }).catch(() => {
      setAutoSmsStatus('idle')
    })
  }, [isCritical, dismissed, pipelineResult?.event_id, alertMessage, cam])

  // Audio alarm
  useEffect(() => {
    if (!isActive || dismissed || !audioEnabled) return

    let stopped = false
    let ctx: AudioContext | null = null

    function playAlarmCycle() {
      if (stopped) return
      try {
        ctx = new AudioContext()
        const gain = ctx.createGain()
        gain.gain.value = 0.07
        gain.connect(ctx.destination)

        const now = ctx.currentTime
        const crit = classification?.criticality === 'CRITICAL'
        const cycleDuration = crit ? 0.5 : 0.8
        const totalCycles = crit ? 20 : 12

        for (let i = 0; i < totalCycles; i++) {
          const t = now + i * cycleDuration
          const osc = ctx.createOscillator()
          osc.type = 'square'
          osc.connect(gain)

          if (crit) {
            osc.frequency.setValueAtTime(960, t)
            osc.frequency.setValueAtTime(720, t + 0.12)
            osc.frequency.setValueAtTime(960, t + 0.24)
            osc.frequency.setValueAtTime(720, t + 0.36)
          } else {
            osc.frequency.setValueAtTime(880, t)
            osc.frequency.setValueAtTime(660, t + 0.2)
            osc.frequency.setValueAtTime(880, t + 0.4)
          }

          osc.start(t)
          osc.stop(t + cycleDuration - 0.05)
        }

        const totalDuration = totalCycles * cycleDuration
        gain.gain.setValueAtTime(0.07, now)
        gain.gain.setValueAtTime(0.07, now + totalDuration - 1)
        gain.gain.exponentialRampToValueAtTime(0.001, now + totalDuration)

        audioCtxRef.current = ctx
      } catch {
        /* audio not available */
      }
    }

    playAlarmCycle()

    return () => {
      stopped = true
      ctx?.close().catch(() => {})
      audioCtxRef.current?.close().catch(() => {})
      audioCtxRef.current = null
    }
  }, [isActive, dismissed, audioEnabled, classification?.criticality])

  if (!isActive || dismissed) return null

  // ── CRITICAL: big 60% overlay ──────────────────────────────────────────
  if (isCritical) {
    return (
      <>
        {/* Full-screen red border flash */}
        <div className="pointer-events-none fixed inset-0 z-[9998]">
          <div className="absolute inset-0 animate-screen-flash-critical rounded-none"
            style={{ boxShadow: 'inset 0 0 120px 40px rgba(239,68,68,0.4)' }} />
          <div className="absolute top-0 left-0 w-48 h-48 animate-corner-pulse-critical"
            style={{ background: 'radial-gradient(ellipse at top left, rgba(239,68,68,0.7) 0%, transparent 70%)' }} />
          <div className="absolute top-0 right-0 w-48 h-48 animate-corner-pulse-critical"
            style={{ background: 'radial-gradient(ellipse at top right, rgba(239,68,68,0.7) 0%, transparent 70%)' }} />
          <div className="absolute bottom-0 left-0 w-48 h-48 animate-corner-pulse-critical"
            style={{ background: 'radial-gradient(ellipse at bottom left, rgba(239,68,68,0.7) 0%, transparent 70%)' }} />
          <div className="absolute bottom-0 right-0 w-48 h-48 animate-corner-pulse-critical"
            style={{ background: 'radial-gradient(ellipse at bottom right, rgba(239,68,68,0.7) 0%, transparent 70%)' }} />
          <div className="absolute top-0 inset-x-0 h-1.5 animate-edge-flash-critical"
            style={{ background: 'linear-gradient(to bottom, rgba(239,68,68,1), transparent)' }} />
          <div className="absolute bottom-0 inset-x-0 h-1.5 animate-edge-flash-critical"
            style={{ background: 'linear-gradient(to top, rgba(239,68,68,1), transparent)' }} />
          <div className="absolute left-0 inset-y-0 w-1.5 animate-edge-flash-critical"
            style={{ background: 'linear-gradient(to right, rgba(239,68,68,1), transparent)' }} />
          <div className="absolute right-0 inset-y-0 w-1.5 animate-edge-flash-critical"
            style={{ background: 'linear-gradient(to left, rgba(239,68,68,1), transparent)' }} />
        </div>

        {/* Big centered overlay (~60% of screen) */}
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/80 backdrop-blur-md">
          <div className="w-[60%] max-w-[800px] max-h-[85vh] rounded-2xl overflow-hidden shadow-2xl shadow-red-500/40 border-2 border-red-500/50 animate-banner-flash-critical flex flex-col">
            {/* Header bar */}
            <div className="bg-red-600 px-6 py-4 flex items-center justify-between shrink-0">
              <div className="flex items-center gap-3">
                <Siren className="h-8 w-8 text-white animate-pulse" />
                <div>
                  <h1 className="text-xl font-black text-white uppercase tracking-wider">
                    Critical Emergency
                  </h1>
                  <p className="text-sm text-white/80 font-mono">
                    Score: {(classification!.score * 100).toFixed(0)}% — Fusion: {fusion!.combined_score.toFixed(3)}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setAudioEnabled(!audioEnabled)}
                  className="rounded-md bg-white/20 hover:bg-white/30 p-2 transition-colors cursor-pointer text-white"
                  title={audioEnabled ? 'Mute' : 'Unmute'}
                >
                  {audioEnabled ? <Volume2 className="h-5 w-5" /> : <VolumeX className="h-5 w-5" />}
                </button>
                <button
                  onClick={() => setDismissed(true)}
                  className="rounded-md bg-white/20 hover:bg-white/30 p-2 transition-colors cursor-pointer text-white"
                  title="Dismiss"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>
            </div>

            {/* Body */}
            <div className="bg-[#1a0000] flex-1 overflow-y-auto p-6 space-y-5">
              {/* Alert message */}
              <div className="rounded-xl bg-red-900/40 border border-red-500/30 p-5">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="h-6 w-6 text-red-400 shrink-0 mt-0.5 animate-pulse" />
                  <p className="text-base leading-relaxed text-white font-medium">
                    {alertMessage}
                  </p>
                </div>
              </div>

              {/* Auto-SMS status */}
              <div className="rounded-xl bg-[#1a1a1a] border border-[#2a2a2a] p-4">
                <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
                  Auto-Notified Groups
                </p>
                <div className="grid grid-cols-2 gap-3">
                  <div className={`rounded-lg p-3 flex items-center gap-3 border ${
                    autoSmsStatus === 'sent' ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-[#222] border-transparent'
                  }`}>
                    <div className={`h-9 w-9 rounded-lg flex items-center justify-center shrink-0 ${
                      autoSmsStatus === 'sent' ? 'bg-emerald-500' : autoSmsStatus === 'sending' ? 'bg-amber-500' : 'bg-gray-700'
                    } text-white`}>
                      <Users className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-white">On-Duty Firefighters</p>
                      <p className="text-xs text-gray-500">
                        {autoSmsStatus === 'sent' ? (
                          <span className="text-emerald-400 flex items-center gap-1"><CheckCircle className="h-3 w-3" /> SMS Sent</span>
                        ) : autoSmsStatus === 'sending' ? (
                          <span className="text-amber-400">Sending...</span>
                        ) : (
                          <span>Pending</span>
                        )}
                      </p>
                    </div>
                  </div>
                  <div className={`rounded-lg p-3 flex items-center gap-3 border ${
                    autoSmsStatus === 'sent' ? 'bg-emerald-500/10 border-emerald-500/30' : 'bg-[#222] border-transparent'
                  }`}>
                    <div className={`h-9 w-9 rounded-lg flex items-center justify-center shrink-0 ${
                      autoSmsStatus === 'sent' ? 'bg-emerald-500' : autoSmsStatus === 'sending' ? 'bg-amber-500' : 'bg-gray-700'
                    } text-white`}>
                      <Radio className="h-4 w-4" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-white">Control Center</p>
                      <p className="text-xs text-gray-500">
                        {autoSmsStatus === 'sent' ? (
                          <span className="text-emerald-400 flex items-center gap-1"><CheckCircle className="h-3 w-3" /> SMS Sent</span>
                        ) : autoSmsStatus === 'sending' ? (
                          <span className="text-amber-400">Sending...</span>
                        ) : (
                          <span>Pending</span>
                        )}
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* Key details */}
              <div className="grid grid-cols-3 gap-3">
                <div className="rounded-lg bg-[#1a1a1a] border border-[#2a2a2a] p-3">
                  <p className="text-xs text-gray-500 mb-1">Camera</p>
                  <p className="text-sm font-bold text-white">{cam?.name ?? '—'}</p>
                  <p className="text-xs text-gray-600 font-mono">{cam?.lat}°N, {cam?.lon}°W</p>
                </div>
                <div className="rounded-lg bg-[#1a1a1a] border border-[#2a2a2a] p-3">
                  <p className="text-xs text-gray-500 mb-1">Weather</p>
                  <p className="text-sm font-bold text-red-400">
                    {pipelineResult?.weather ? `${pipelineResult.weather.wind_speed.toFixed(1)} m/s · ${pipelineResult.weather.humidity.toFixed(0)}% humidity` : '—'}
                  </p>
                  <p className="text-xs text-gray-600">Spread risk: {pipelineResult?.weather ? `${(pipelineResult.weather.spread_risk * 100).toFixed(0)}%` : '—'}</p>
                </div>
                <div className="rounded-lg bg-[#1a1a1a] border border-[#2a2a2a] p-3">
                  <p className="text-xs text-gray-500 mb-1">Thermal</p>
                  <p className="text-sm font-bold text-red-400">
                    {pipelineResult?.satellite?.hotspot_detected ? `${((pipelineResult.satellite.raw as Record<string, unknown>)?.hotspots as unknown[])?.length ?? 0} hotspot(s)` : 'None'}
                  </p>
                  <p className="text-xs text-gray-600">Confidence: {pipelineResult?.satellite ? `${(pipelineResult.satellite.thermal_confidence * 100).toFixed(0)}%` : '—'}</p>
                </div>
              </div>

              {/* Scene reasoning */}
              {pipelineResult?.reasoning && (
                <div className="rounded-lg bg-[#1a1a1a] border border-[#2a2a2a] p-4">
                  <p className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">Scene Analysis</p>
                  <p className="text-sm leading-relaxed text-gray-300">{pipelineResult.reasoning.scene_description}</p>
                </div>
              )}

              {/* Evacuate area residents button */}
              <button
                onClick={() => setSmsOpen(true)}
                className="w-full flex items-center justify-center gap-3 rounded-xl bg-red-600 hover:bg-red-700 px-6 py-4 text-base font-bold text-white uppercase tracking-wider transition-colors cursor-pointer shadow-lg shadow-red-500/20"
              >
                <MapPin className="h-5 w-5" />
                Alert Area Residents — Send Evacuation SMS
              </button>
            </div>
          </div>
        </div>

        {/* SMS Panel for area residents only */}
        {smsOpen && <SMSPanel onClose={() => setSmsOpen(false)} residentsOnly />}
      </>
    )
  }

  // ── HIGH: standard top banner ──────────────────────────────────────────
  return (
    <>
      {/* Corner pulse overlays */}
      <div className="pointer-events-none fixed inset-0 z-[9998]">
        <div className="absolute top-0 left-0 w-32 h-32 animate-corner-pulse"
          style={{ background: 'radial-gradient(ellipse at top left, rgba(239,68,68,0.5) 0%, transparent 70%)' }} />
        <div className="absolute top-0 right-0 w-32 h-32 animate-corner-pulse"
          style={{ background: 'radial-gradient(ellipse at top right, rgba(239,68,68,0.5) 0%, transparent 70%)' }} />
        <div className="absolute bottom-0 left-0 w-32 h-32 animate-corner-pulse"
          style={{ background: 'radial-gradient(ellipse at bottom left, rgba(239,68,68,0.5) 0%, transparent 70%)' }} />
        <div className="absolute bottom-0 right-0 w-32 h-32 animate-corner-pulse"
          style={{ background: 'radial-gradient(ellipse at bottom right, rgba(239,68,68,0.5) 0%, transparent 70%)' }} />
        <div className="absolute top-0 inset-x-0 h-1 animate-edge-flash"
          style={{ background: 'linear-gradient(to bottom, rgba(239,68,68,0.8), transparent)' }} />
        <div className="absolute bottom-0 inset-x-0 h-1 animate-edge-flash"
          style={{ background: 'linear-gradient(to top, rgba(239,68,68,0.8), transparent)' }} />
      </div>

      {/* Top banner */}
      <div className="fixed top-0 inset-x-0 z-[9999] animate-banner-flash">
        <div className="flex items-center justify-between px-5 py-3 bg-red-500 text-white shadow-lg shadow-red-500/30">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <AlertTriangle className="h-6 w-6 shrink-0 animate-pulse" />
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-2 mb-0.5">
                <span className="text-sm font-bold uppercase tracking-wider">
                  FIRE ALERT — {classification!.criticality}
                </span>
                <span className="text-xs font-mono bg-white/20 rounded px-1.5 py-0.5">
                  Score: {(classification!.score * 100).toFixed(0)}%
                </span>
              </div>
              <p className="text-xs text-white/90 truncate">{alertMessage}</p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0 ml-4">
            <button
              onClick={() => setSmsOpen(true)}
              className="flex items-center gap-1.5 rounded-md bg-white/20 hover:bg-white/30 px-3 py-2 text-xs font-semibold uppercase tracking-wider transition-colors cursor-pointer"
            >
              <MessageSquare className="h-4 w-4" />
              Send SMS
            </button>
            <button
              onClick={() => setAudioEnabled(!audioEnabled)}
              className="rounded-md bg-white/20 hover:bg-white/30 p-2 transition-colors cursor-pointer"
              title={audioEnabled ? 'Mute' : 'Unmute'}
            >
              {audioEnabled ? <Volume2 className="h-4 w-4" /> : <VolumeX className="h-4 w-4" />}
            </button>
            <button
              onClick={() => setDismissed(true)}
              className="rounded-md bg-white/20 hover:bg-white/30 p-2 transition-colors cursor-pointer"
              title="Dismiss alert"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      {smsOpen && <SMSPanel onClose={() => setSmsOpen(false)} />}
    </>
  )
}
