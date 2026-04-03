import { useState } from 'react'
import { Radio, RefreshCw, AlertTriangle, Play, ChevronDown, Crosshair } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import { usePipeline, DEMO_LABELS, type DemoScenario } from '../context/PipelineContext'
import WeatherPanel from './WeatherPanel'

const CRITICALITY_COLORS: Record<string, string> = {
  LOW: 'text-emerald-400 bg-emerald-400/10',
  MEDIUM: 'text-yellow-400 bg-yellow-400/10',
  HIGH: 'text-amber-400 bg-amber-400/10',
  CRITICAL: 'text-red-400 bg-red-400/10',
}

const SCENARIO_KEYS: DemoScenario[] = ['clear', 'smoke', 'fire_high', 'critical']

export default function Sidebar() {
  const { theme } = useTheme()
  const dark = theme === 'dark' || theme === 'verizon'
  const {
    cameras,
    selectedCamera,
    setSelectedCamera,
    pipelineResult,
    isAnalyzing,
    runAnalysis,
    loadDemo,
    error,
    droneStations,
  } = usePipeline()

  const [selectedScenario, setSelectedScenario] = useState<DemoScenario>('fire_high')

  const fusion = pipelineResult?.fusion
  const classification = pipelineResult?.classification
  const suggestion = pipelineResult?.suggestion

  return (
    <aside
      className={`w-[320px] shrink-0 flex flex-col border-r overflow-y-auto ${
        dark ? 'bg-[#0a0a0a] border-[#1e1e1e]' : 'bg-gray-50 border-gray-200'
      }`}
    >
      {/* Camera Nodes */}
      <div className="p-4">
        <div className="flex items-center justify-between mb-3">
          <span className={`text-xs font-semibold uppercase tracking-wider ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
            Camera Nodes
          </span>
          <span className={`text-xs font-medium rounded-full px-2 py-0.5 ${dark ? 'bg-[#1a1a1a] text-gray-400' : 'bg-gray-200 text-gray-500'}`}>
            {cameras.length}
          </span>
        </div>

        <div className="flex flex-col gap-1.5">
          {cameras.map(cam => (
            <button
              key={cam.id}
              onClick={() => setSelectedCamera(cam.id)}
              className={`w-full flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-left transition-colors cursor-pointer ${
                selectedCamera === cam.id
                  ? dark ? 'bg-brand/15 border border-brand/30' : 'bg-amber-50 border border-amber-200'
                  : dark ? 'hover:bg-[#141414] border border-transparent' : 'hover:bg-gray-100 border border-transparent'
              }`}
            >
              <Radio className={`h-4 w-4 shrink-0 ${selectedCamera === cam.id ? 'text-brand' : dark ? 'text-gray-600' : 'text-gray-400'}`} />
              <div className="min-w-0 flex-1">
                <p className={`text-sm font-medium truncate ${selectedCamera === cam.id ? (dark ? 'text-white' : 'text-gray-900') : (dark ? 'text-gray-300' : 'text-gray-700')}`}>
                  {cam.name}
                </p>
                <p className={`text-xs ${dark ? 'text-gray-600' : 'text-gray-400'}`}>{cam.code}</p>
              </div>
              <span className={`h-2.5 w-2.5 rounded-full shrink-0 ${cam.online ? 'bg-emerald-500' : 'bg-gray-500'}`} />
            </button>
          ))}
        </div>

        {/* Analyze button */}
        <button
          onClick={runAnalysis}
          disabled={isAnalyzing}
          className="w-full flex items-center justify-center gap-2 rounded-lg bg-brand px-3 py-2.5 mt-3 text-xs font-semibold uppercase tracking-wider text-white hover:bg-brand-light transition-colors cursor-pointer disabled:opacity-50"
        >
          <Play className="h-3.5 w-3.5" />
          {isAnalyzing ? 'Analyzing...' : 'Run Analysis'}
        </button>

        {/* Demo scenario picker */}
        <div className="mt-2">
          <span className={`text-[11px] font-semibold uppercase tracking-wider block mb-1.5 ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
            Demo Scenarios
          </span>
          <div className="flex flex-col gap-1.5">
            {SCENARIO_KEYS.map(key => (
              <button
                key={key}
                onClick={() => {
                  setSelectedScenario(key)
                  loadDemo(key)
                }}
                className={`w-full flex items-center gap-2 rounded-lg px-3 py-2 text-xs font-medium text-left transition-colors cursor-pointer ${
                  selectedScenario === key && pipelineResult
                    ? dark ? 'bg-brand/15 border border-brand/30 text-brand' : 'bg-amber-50 border border-amber-200 text-amber-700'
                    : dark ? 'bg-[#1a1a1a] border border-transparent text-gray-400 hover:text-white hover:bg-[#222]' : 'bg-gray-100 border border-transparent text-gray-600 hover:text-gray-900 hover:bg-gray-200'
                }`}
              >
                <ChevronDown className={`h-3 w-3 shrink-0 transition-transform ${selectedScenario === key && pipelineResult ? 'rotate-0 text-brand' : '-rotate-90'}`} />
                {DEMO_LABELS[key]}
              </button>
            ))}
          </div>
        </div>

        {error && (
          <p className="mt-2 text-xs text-red-400 bg-red-400/10 rounded-md px-2 py-1.5">{error}</p>
        )}
      </div>

      {/* Drone Stations */}
      <div className={`px-4 pb-4 border-t pt-3 ${dark ? 'border-[#1e1e1e]' : 'border-gray-200'}`}>
        <div className="flex items-center justify-between mb-2">
          <span className={`text-xs font-semibold uppercase tracking-wider ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
            Drone Stations
          </span>
          <span className={`text-xs font-medium rounded-full px-2 py-0.5 ${dark ? 'bg-[#1a1a1a] text-gray-400' : 'bg-gray-200 text-gray-500'}`}>
            {droneStations.length}
          </span>
        </div>
        <div className="flex flex-col gap-1">
          {droneStations.map(ds => (
            <div
              key={ds.id}
              className={`flex items-center gap-2.5 rounded-lg px-3 py-2 ${dark ? 'bg-[#141414]' : 'bg-white border border-gray-100'}`}
            >
              <Crosshair className={`h-4 w-4 shrink-0 ${ds.status === 'ready' ? 'text-emerald-500' : 'text-red-400'}`} />
              <div className="min-w-0 flex-1">
                <p className={`text-xs font-medium truncate ${dark ? 'text-gray-300' : 'text-gray-700'}`}>{ds.name}</p>
                <p className={`text-[11px] ${dark ? 'text-gray-600' : 'text-gray-400'}`}>
                  {ds.drones} drone{ds.drones !== 1 ? 's' : ''} &middot; {ds.payloads.join(', ')}
                </p>
              </div>
              <span className={`h-2.5 w-2.5 rounded-full shrink-0 ${ds.status === 'ready' ? 'bg-emerald-500' : 'bg-red-400 animate-pulse'}`} />
            </div>
          ))}
        </div>
      </div>

      {/* Weather Intel */}
      <WeatherPanel />

      {/* Recent Alerts / Pipeline Result */}
      <div className={`p-4 border-t flex-1 ${dark ? 'border-[#1e1e1e]' : 'border-gray-200'}`}>
        <div className="flex items-center justify-between mb-3">
          <span className={`text-xs font-semibold uppercase tracking-wider ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
            Recent Alerts
          </span>
          <RefreshCw className={`h-3.5 w-3.5 ${dark ? 'text-gray-600' : 'text-gray-400'}`} />
        </div>

        {fusion && classification ? (
          <div className={`rounded-lg p-3 border ${dark ? 'bg-[#141414] border-[#1e1e1e]' : 'bg-white border-gray-200'}`}>
            <div className="flex items-center gap-2 mb-2">
              <AlertTriangle className={`h-4 w-4 ${CRITICALITY_COLORS[classification.criticality]?.split(' ')[0] ?? 'text-gray-400'}`} />
              <span className={`text-xs font-bold uppercase px-2 py-0.5 rounded ${CRITICALITY_COLORS[classification.criticality] ?? ''}`}>
                {classification.criticality}
              </span>
              <span className={`text-xs ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
                {(classification.score * 100).toFixed(0)}%
              </span>
            </div>
            <p className={`text-xs leading-relaxed mb-2 ${dark ? 'text-gray-400' : 'text-gray-600'}`}>
              {classification.reasoning}
            </p>
            <div className={`text-xs rounded px-2 py-1.5 font-medium ${
              fusion.status === 'CONFIRMED'
                ? 'bg-emerald-500/10 text-emerald-400'
                : 'bg-red-500/10 text-red-400'
            }`}>
              {fusion.status} — Score: {fusion.combined_score.toFixed(2)}
            </div>

            {suggestion && (
              <div className={`mt-2 pt-2 border-t ${dark ? 'border-[#1e1e1e]' : 'border-gray-100'}`}>
                <p className={`text-[11px] font-semibold uppercase tracking-wider mb-1.5 ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
                  Alert
                </p>
                <p className={`text-xs leading-relaxed ${dark ? 'text-gray-400' : 'text-gray-600'}`}>
                  {suggestion.alert_message}
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-6">
            <div className={`h-12 w-12 rounded-full flex items-center justify-center mb-3 ${dark ? 'bg-[#141414]' : 'bg-gray-100'}`}>
              <RefreshCw className={`h-5 w-5 ${dark ? 'text-gray-600' : 'text-gray-400'}`} />
            </div>
            <p className={`text-xs font-medium uppercase tracking-wider ${dark ? 'text-gray-600' : 'text-gray-400'}`}>
              No Active Threats
            </p>
          </div>
        )}
      </div>
    </aside>
  )
}
