import { useState, useMemo } from 'react'
import {
  FileText, Copy, Share2, Download, Check,
  CheckCircle, XCircle, AlertTriangle, Shield,
  Camera, Satellite, Cloud, Merge, Brain, Gauge, Lightbulb, Bell,
  Pencil, Clock,
} from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import { usePipeline } from '../context/PipelineContext'

type Verdict = 'true_positive' | 'false_positive' | 'true_negative' | 'false_negative' | null

const VERDICT_CONFIG: Record<Exclude<Verdict, null>, { label: string; short: string; color: string; bg: string; icon: React.ReactNode; description: string }> = {
  true_positive: {
    label: 'True Positive',
    short: 'TP',
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/10 border-emerald-500/30 hover:bg-emerald-500/20',
    icon: <CheckCircle className="h-5 w-5" />,
    description: 'Alarm was correct — real fire/incident confirmed',
  },
  false_positive: {
    label: 'False Positive',
    short: 'FP',
    color: 'text-amber-400',
    bg: 'bg-amber-500/10 border-amber-500/30 hover:bg-amber-500/20',
    icon: <XCircle className="h-5 w-5" />,
    description: 'Alarm triggered but no real fire — false alarm',
  },
  true_negative: {
    label: 'True Negative',
    short: 'TN',
    color: 'text-blue-400',
    bg: 'bg-blue-500/10 border-blue-500/30 hover:bg-blue-500/20',
    icon: <Shield className="h-5 w-5" />,
    description: 'No alarm and no fire — system correctly quiet',
  },
  false_negative: {
    label: 'False Negative',
    short: 'FN',
    color: 'text-red-400',
    bg: 'bg-red-500/10 border-red-500/30 hover:bg-red-500/20',
    icon: <AlertTriangle className="h-5 w-5" />,
    description: 'No alarm but fire was real — system missed it',
  },
}

function windDir(deg: number): string {
  const dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
  return dirs[Math.round(deg / 45) % 8]
}

export default function IncidentReport() {
  const { theme } = useTheme()
  const dark = theme === 'dark' || theme === 'verizon'
  const { pipelineResult, cameras, selectedCamera } = usePipeline()

  const [verdict, setVerdict] = useState<Verdict>(null)
  const [analystName, setAnalystName] = useState('Khoi Duong')
  const [notes, setNotes] = useState('')
  const [editingName, setEditingName] = useState(false)
  const [copied, setCopied] = useState(false)
  const [shared, setShared] = useState(false)

  const cam = cameras.find(c => c.id === selectedCamera)
  const r = pipelineResult
  const timestamp = useMemo(() => new Date().toLocaleString('en-US', {
    weekday: 'short', year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit', second: '2-digit',
  }), [r?.event_id])

  const card = `rounded-xl border p-4 ${dark ? 'bg-[#141414] border-[#1e1e1e]' : 'bg-white border-gray-200'}`
  const sectionTitle = `text-[11px] font-semibold uppercase tracking-wider mb-3 flex items-center gap-2 ${dark ? 'text-gray-500' : 'text-gray-400'}`
  const label = `text-xs ${dark ? 'text-gray-500' : 'text-gray-400'}`
  const value = `text-sm font-semibold ${dark ? 'text-white' : 'text-gray-900'}`

  const buildReportText = (): string => {
    if (!r) return 'No pipeline data available.'
    const lines: string[] = [
      '═══════════════════════════════════════════',
      '  WILDFIRE WATCH MVP — INCIDENT REPORT',
      '═══════════════════════════════════════════',
      '',
      `Report ID:     ${r.event_id}`,
      `Timestamp:     ${timestamp}`,
      `Camera:        ${cam?.name ?? 'Unknown'} (${cam?.code ?? '—'})`,
      `Location:      ${cam?.lat ?? '—'}°N, ${cam?.lon ?? '—'}°W`,
      `Analyst:       ${analystName}`,
      verdict ? `Verdict:       ${VERDICT_CONFIG[verdict].label}` : 'Verdict:       Pending',
      '',
      '── SENSOR DATA ────────────────────────────',
      `Camera YOLO:   ${r.camera ? `${(r.camera.confidence * 100).toFixed(0)}% confidence, ${r.camera.detected ? 'DETECTED' : 'Clear'}` : '—'}`,
      `Satellite:     ${r.satellite ? `${(r.satellite.thermal_confidence * 100).toFixed(0)}% thermal, ${r.satellite.hotspot_detected ? 'HOTSPOT' : 'Clear'}` : '—'}`,
      `Weather:       ${r.weather ? `Wind ${r.weather.wind_speed.toFixed(1)} m/s ${windDir(r.weather.wind_direction)}, Humidity ${r.weather.humidity.toFixed(0)}%, Spread Risk ${(r.weather.spread_risk * 100).toFixed(0)}%` : '—'}`,
      '',
      '── FUSION DECISION ────────────────────────',
      `Status:        ${r.fusion?.status ?? '—'}`,
      `Score:         ${r.fusion?.combined_score?.toFixed(3) ?? '—'}`,
      `Reason:        ${r.fusion?.reason ?? '—'}`,
      '',
      '── CLASSIFICATION ─────────────────────────',
      `Criticality:   ${r.classification?.criticality ?? '—'}`,
      `Score:         ${r.classification ? `${(r.classification.score * 100).toFixed(0)}%` : '—'}`,
      `Reasoning:     ${r.classification?.reasoning ?? '—'}`,
      '',
      '── SCENE ANALYSIS ─────────────────────────',
      r.reasoning?.scene_description ?? '—',
      '',
      ...(r.reasoning?.key_observations?.map((o, i) => `  ${i + 1}. ${o}`) ?? []),
      '',
      '── ACTION PLAN ────────────────────────────',
      ...(r.suggestion?.action_plan?.map((a, i) => `  ${i + 1}. ${a}`) ?? []),
      '',
      '── ALERT MESSAGE ──────────────────────────',
      r.suggestion?.alert_message ?? '—',
      '',
      '── RESOURCES ──────────────────────────────',
      ...(r.suggestion?.recommended_resources?.map(res => `  • ${res}`) ?? []),
    ]

    if (notes.trim()) {
      lines.push('', '── ANALYST NOTES ──────────────────────────', notes)
    }

    lines.push('', '═══════════════════════════════════════════')
    return lines.join('\n')
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(buildReportText())
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleShare = () => {
    const text = buildReportText()
    if (navigator.share) {
      navigator.share({ title: `Incident Report — ${r?.event_id}`, text })
    } else {
      navigator.clipboard.writeText(text)
    }
    setShared(true)
    setTimeout(() => setShared(false), 2000)
  }

  const handleExport = () => {
    const blob = new Blob([buildReportText()], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `incident-report-${r?.event_id ?? 'unknown'}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  if (!r) {
    return (
      <div className={`rounded-xl border flex items-center justify-center py-20 ${dark ? 'bg-[#111] border-[#1e1e1e]' : 'bg-white border-gray-200'}`}>
        <div className="text-center">
          <FileText className={`h-12 w-12 mx-auto mb-3 ${dark ? 'text-gray-700' : 'text-gray-300'}`} />
          <p className={`text-sm font-medium ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
            Run a demo scenario or analysis to generate a report
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {/* Report header + actions */}
      <div className={card}>
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <FileText className="h-5 w-5 text-brand" />
              <h2 className={`text-lg font-bold ${dark ? 'text-white' : 'text-gray-900'}`}>
                Incident Report
              </h2>
              {verdict && (
                <span className={`text-xs font-bold uppercase px-2 py-0.5 rounded border ${VERDICT_CONFIG[verdict].bg} ${VERDICT_CONFIG[verdict].color}`}>
                  {VERDICT_CONFIG[verdict].short} — {VERDICT_CONFIG[verdict].label}
                </span>
              )}
            </div>
            <div className={`flex items-center gap-4 text-xs ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
              <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{timestamp}</span>
              <span>ID: {r.event_id}</span>
              <span>{cam?.name ?? 'Unknown'} ({cam?.code})</span>
              <span>{cam?.lat}°N, {cam?.lon}°W</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={handleCopy}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium transition-colors cursor-pointer ${
                dark ? 'bg-[#1a1a1a] text-gray-400 hover:text-white' : 'bg-gray-100 text-gray-600 hover:text-gray-900'
              }`}>
              {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
              {copied ? 'Copied' : 'Copy'}
            </button>
            <button onClick={handleShare}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium transition-colors cursor-pointer ${
                dark ? 'bg-[#1a1a1a] text-gray-400 hover:text-white' : 'bg-gray-100 text-gray-600 hover:text-gray-900'
              }`}>
              {shared ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Share2 className="h-3.5 w-3.5" />}
              {shared ? 'Shared' : 'Share'}
            </button>
            <button onClick={handleExport}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium transition-colors cursor-pointer ${
                dark ? 'bg-[#1a1a1a] text-gray-400 hover:text-white' : 'bg-gray-100 text-gray-600 hover:text-gray-900'
              }`}>
              <Download className="h-3.5 w-3.5" />
              Export
            </button>
          </div>
        </div>

        {/* Analyst */}
        <div className="flex items-center gap-2">
          <span className={label}>Analyst:</span>
          {editingName ? (
            <input
              value={analystName}
              onChange={e => setAnalystName(e.target.value)}
              onBlur={() => setEditingName(false)}
              onKeyDown={e => e.key === 'Enter' && setEditingName(false)}
              autoFocus
              className={`text-sm font-semibold px-2 py-0.5 rounded border outline-none ${
                dark ? 'bg-[#1a1a1a] border-brand/50 text-white' : 'bg-gray-50 border-brand/50 text-gray-900'
              }`}
            />
          ) : (
            <button onClick={() => setEditingName(true)} className={`flex items-center gap-1 ${value} hover:text-brand transition-colors cursor-pointer`}>
              {analystName}
              <Pencil className="h-3 w-3 opacity-50" />
            </button>
          )}
        </div>
      </div>

      {/* Verdict buttons */}
      <div className={card}>
        <p className={sectionTitle}><Gauge className="h-4 w-4" /> Alarm Verdict</p>
        <div className="grid grid-cols-4 gap-2">
          {(Object.keys(VERDICT_CONFIG) as Exclude<Verdict, null>[]).map(key => {
            const cfg = VERDICT_CONFIG[key]
            const active = verdict === key
            return (
              <button
                key={key}
                onClick={() => setVerdict(active ? null : key)}
                className={`flex flex-col items-center gap-2 rounded-xl p-3 border transition-colors cursor-pointer ${
                  active
                    ? `${cfg.bg} ${cfg.color}`
                    : dark ? 'bg-[#1a1a1a] border-transparent text-gray-500 hover:text-gray-300 hover:bg-[#222]' : 'bg-gray-50 border-transparent text-gray-400 hover:text-gray-700 hover:bg-gray-100'
                }`}
              >
                {cfg.icon}
                <span className="text-xs font-bold uppercase tracking-wider">{cfg.short}</span>
                <span className={`text-[11px] leading-tight text-center ${active ? '' : dark ? 'text-gray-600' : 'text-gray-400'}`}>
                  {cfg.description}
                </span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Sensor data grid */}
      <div className="grid grid-cols-3 gap-3">
        {/* Camera */}
        <div className={card}>
          <p className={sectionTitle}><Camera className="h-4 w-4" /> Camera Agent</p>
          <div className="space-y-2">
            <div><span className={label}>YOLO Confidence</span><p className={value}>{r.camera ? `${(r.camera.confidence * 100).toFixed(1)}%` : '—'}</p></div>
            <div><span className={label}>Detection</span><p className={`text-sm font-bold ${r.camera?.detected ? 'text-red-400' : 'text-emerald-400'}`}>{r.camera?.detected ? 'FIRE DETECTED' : 'Clear'}</p></div>
            <div><span className={label}>Latency</span><p className={value}>{r.camera?.latency_ms ? `${r.camera.latency_ms.toFixed(0)} ms` : '—'}</p></div>
          </div>
        </div>

        {/* Satellite */}
        <div className={card}>
          <p className={sectionTitle}><Satellite className="h-4 w-4" /> Satellite Agent</p>
          <div className="space-y-2">
            <div><span className={label}>Thermal Confidence</span><p className={value}>{r.satellite ? `${(r.satellite.thermal_confidence * 100).toFixed(1)}%` : '—'}</p></div>
            <div><span className={label}>Hotspot</span><p className={`text-sm font-bold ${r.satellite?.hotspot_detected ? 'text-red-400' : 'text-emerald-400'}`}>{r.satellite?.hotspot_detected ? 'DETECTED' : 'None'}</p></div>
            <div><span className={label}>Latency</span><p className={value}>{r.satellite?.latency_ms ? `${r.satellite.latency_ms.toFixed(0)} ms` : '—'}</p></div>
          </div>
        </div>

        {/* Weather */}
        <div className={card}>
          <p className={sectionTitle}><Cloud className="h-4 w-4" /> Weather Agent</p>
          <div className="space-y-2">
            <div><span className={label}>Wind</span><p className={value}>{r.weather ? `${r.weather.wind_speed.toFixed(1)} m/s ${windDir(r.weather.wind_direction)}` : '—'}</p></div>
            <div><span className={label}>Humidity</span><p className={`text-sm font-bold ${r.weather && r.weather.humidity < 25 ? 'text-red-400' : dark ? 'text-white' : 'text-gray-900'}`}>{r.weather ? `${r.weather.humidity.toFixed(0)}%` : '—'}</p></div>
            <div><span className={label}>Spread Risk</span><p className={`text-sm font-bold ${r.weather && r.weather.spread_risk >= 0.75 ? 'text-red-400' : r.weather && r.weather.spread_risk >= 0.5 ? 'text-amber-400' : dark ? 'text-white' : 'text-gray-900'}`}>{r.weather ? `${(r.weather.spread_risk * 100).toFixed(0)}%` : '—'}</p></div>
          </div>
        </div>
      </div>

      {/* Fusion + Classification */}
      <div className="grid grid-cols-2 gap-3">
        <div className={card}>
          <p className={sectionTitle}><Merge className="h-4 w-4" /> Fusion Decision</p>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className={`text-sm font-bold uppercase px-2 py-0.5 rounded ${
                r.fusion?.status === 'CONFIRMED' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'
              }`}>{r.fusion?.status ?? '—'}</span>
              <span className={value}>Score: {r.fusion?.combined_score?.toFixed(3) ?? '—'}</span>
            </div>
            <p className={`text-sm leading-relaxed ${dark ? 'text-gray-400' : 'text-gray-600'}`}>{r.fusion?.reason}</p>
          </div>
        </div>
        <div className={card}>
          <p className={sectionTitle}><Gauge className="h-4 w-4" /> Classification</p>
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span className={`text-sm font-bold uppercase px-2 py-0.5 rounded ${
                r.classification?.criticality === 'CRITICAL' ? 'bg-red-500/10 text-red-400' :
                r.classification?.criticality === 'HIGH' ? 'bg-amber-500/10 text-amber-400' :
                r.classification?.criticality === 'MEDIUM' ? 'bg-yellow-500/10 text-yellow-400' :
                'bg-emerald-500/10 text-emerald-400'
              }`}>{r.classification?.criticality ?? '—'}</span>
              <span className={value}>{r.classification ? `${(r.classification.score * 100).toFixed(0)}%` : '—'}</span>
            </div>
            <p className={`text-sm leading-relaxed ${dark ? 'text-gray-400' : 'text-gray-600'}`}>{r.classification?.reasoning}</p>
          </div>
        </div>
      </div>

      {/* Scene Analysis */}
      {r.reasoning && (
        <div className={card}>
          <p className={sectionTitle}><Brain className="h-4 w-4" /> Scene Analysis (VLM)</p>
          <p className={`text-sm leading-relaxed mb-3 ${dark ? 'text-gray-300' : 'text-gray-700'}`}>{r.reasoning.scene_description}</p>
          {r.reasoning.key_observations.length > 0 && (
            <ul className="space-y-1.5">
              {r.reasoning.key_observations.map((obs, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-brand text-xs font-bold mt-0.5 shrink-0">{i + 1}.</span>
                  <span className={`text-sm leading-relaxed ${dark ? 'text-gray-400' : 'text-gray-600'}`}>{obs}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* Action Plan + Resources */}
      {r.suggestion && (
        <div className="grid grid-cols-2 gap-3">
          <div className={card}>
            <p className={sectionTitle}><Lightbulb className="h-4 w-4" /> Action Plan</p>
            <ul className="space-y-1.5">
              {r.suggestion.action_plan.map((action, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-emerald-400 text-xs font-bold mt-0.5 shrink-0">{i + 1}.</span>
                  <span className={`text-sm leading-relaxed ${dark ? 'text-gray-400' : 'text-gray-600'}`}>{action}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className={card}>
            <p className={sectionTitle}><Bell className="h-4 w-4" /> Alert &amp; Resources</p>
            <div className={`rounded-lg p-3 mb-3 ${dark ? 'bg-[#1a1a1a]' : 'bg-gray-50'}`}>
              <p className={`text-sm leading-relaxed ${dark ? 'text-gray-300' : 'text-gray-700'}`}>{r.suggestion.alert_message}</p>
            </div>
            {r.suggestion.recommended_resources.length > 0 && (
              <ul className="space-y-1">
                {r.suggestion.recommended_resources.map((res, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-blue-400 text-xs mt-0.5 shrink-0">&#x25B8;</span>
                    <span className={`text-sm ${dark ? 'text-gray-400' : 'text-gray-600'}`}>{res}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

      {/* Analyst Notes */}
      <div className={card}>
        <p className={sectionTitle}><Pencil className="h-4 w-4" /> Analyst Notes</p>
        <textarea
          value={notes}
          onChange={e => setNotes(e.target.value)}
          placeholder="Add observations, corrections, or follow-up actions..."
          rows={4}
          className={`w-full rounded-lg p-3 text-sm leading-relaxed resize-y outline-none border ${
            dark
              ? 'bg-[#1a1a1a] border-[#2a2a2a] text-gray-300 placeholder-gray-600 focus:border-brand/50'
              : 'bg-gray-50 border-gray-200 text-gray-700 placeholder-gray-400 focus:border-brand/50'
          }`}
        />
      </div>
    </div>
  )
}
