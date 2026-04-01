import { useState } from 'react'
import { Sparkles, Play } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'

export default function VisualReasoning() {
  const { theme } = useTheme()
  const dark = theme === 'dark'
  const [simulating, setSimulating] = useState(false)
  const [output, setOutput] = useState('Awaiting next frame analysis...')

  const handleSimulate = () => {
    setSimulating(true)
    setOutput('Analyzing frame #2847 from Sierra Peak North...')
    setTimeout(() => {
      setOutput(
        'Frame #2847 — No anomalies detected. Vegetation baseline nominal. ' +
        'Thermal signature within expected range. Wind patterns: SW 8mph. ' +
        'Humidity: 42%. No smoke plume geometry identified. Confidence: 0.02 (CLEAR)'
      )
      setSimulating(false)
    }, 2500)
  }

  return (
    <div
      className={`rounded-xl border overflow-hidden flex flex-col ${
        dark ? 'bg-[#111] border-[#1e1e1e]' : 'bg-white border-gray-200'
      }`}
    >
      <div className={`flex items-center justify-between px-4 py-2.5 border-b ${dark ? 'border-[#1e1e1e]' : 'border-gray-100'}`}>
        <div className="flex items-center gap-2">
          <Sparkles className="h-3.5 w-3.5 text-brand" />
          <span className={`text-xs font-semibold uppercase tracking-wider ${dark ? 'text-gray-400' : 'text-gray-600'}`}>
            Live Visual Reasoning
          </span>
        </div>
        <button
          onClick={handleSimulate}
          disabled={simulating}
          className="flex items-center gap-1.5 rounded-md bg-brand/15 px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-brand hover:bg-brand/25 transition-colors cursor-pointer disabled:opacity-50"
        >
          <Play className="h-3 w-3" />
          Simulate Smoke
        </button>
      </div>

      <div className="flex-1 p-4 min-h-[80px]">
        <p className={`text-xs leading-relaxed font-mono ${dark ? 'text-gray-400' : 'text-gray-600'}`}>
          {simulating && (
            <span className="inline-block h-3 w-3 mr-2 border-2 border-brand border-t-transparent rounded-full animate-spin align-middle" />
          )}
          {output}
        </p>
      </div>
    </div>
  )
}
