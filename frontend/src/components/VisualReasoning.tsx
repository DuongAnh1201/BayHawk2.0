import { useState } from 'react'
import { Sparkles, Play, Eye, ListChecks } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import { usePipeline } from '../context/PipelineContext'

export default function VisualReasoning() {
  const { theme } = useTheme()
  const dark = theme === 'dark' || theme === 'verizon'
  const { pipelineResult, isAnalyzing, runAnalysis, loadDemo } = usePipeline()
  const [showObservations, setShowObservations] = useState(false)

  const reasoning = pipelineResult?.reasoning
  const suggestion = pipelineResult?.suggestion

  return (
    <div className={`rounded-xl border overflow-hidden flex flex-col ${dark ? 'bg-[#111] border-[#1e1e1e]' : 'bg-white border-gray-200'}`}>
      <div className={`flex items-center justify-between px-4 py-2.5 border-b shrink-0 ${dark ? 'border-[#1e1e1e]' : 'border-gray-100'}`}>
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-brand" />
          <span className={`text-sm font-semibold uppercase tracking-wider ${dark ? 'text-gray-400' : 'text-gray-600'}`}>
            Live Visual Reasoning
          </span>
        </div>
        <div className="flex items-center gap-2">
          {reasoning && (
            <button
              onClick={() => setShowObservations(!showObservations)}
              className={`flex items-center gap-1 rounded-md px-2.5 py-1.5 text-xs font-semibold uppercase tracking-wider transition-colors cursor-pointer ${
                showObservations
                  ? 'bg-brand/20 text-brand'
                  : dark ? 'bg-[#1a1a1a] text-gray-400 hover:text-white' : 'bg-gray-100 text-gray-500 hover:text-gray-900'
              }`}
            >
              <ListChecks className="h-3.5 w-3.5" />
              Details
            </button>
          )}
          <button
            onClick={() => pipelineResult ? runAnalysis() : loadDemo('fire_high')}
            disabled={isAnalyzing}
            className="flex items-center gap-1.5 rounded-md bg-brand/15 px-3 py-1.5 text-xs font-semibold uppercase tracking-wider text-brand hover:bg-brand/25 transition-colors cursor-pointer disabled:opacity-50"
          >
            <Play className="h-3.5 w-3.5" />
            Simulate Smoke
          </button>
        </div>
      </div>

      <div className="flex-1 p-4 overflow-y-auto">
        {isAnalyzing ? (
          <div className="flex items-center gap-2">
            <span className="inline-block h-4 w-4 border-2 border-brand border-t-transparent rounded-full animate-spin" />
            <p className={`text-sm font-mono ${dark ? 'text-gray-400' : 'text-gray-600'}`}>
              Running VLM analysis on camera frame...
            </p>
          </div>
        ) : reasoning ? (
          <div className="space-y-3">
            {/* Scene description */}
            <div>
              <div className="flex items-center gap-1.5 mb-1.5">
                <Eye className={`h-3.5 w-3.5 ${dark ? 'text-gray-500' : 'text-gray-400'}`} />
                <span className={`text-[11px] font-semibold uppercase tracking-wider ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
                  Scene Analysis
                </span>
              </div>
              <p className={`text-sm leading-relaxed ${dark ? 'text-gray-300' : 'text-gray-700'}`}>
                {reasoning.scene_description}
              </p>
            </div>

            {/* Key observations (expandable) */}
            {showObservations && reasoning.key_observations.length > 0 && (
              <div className={`border-t pt-3 ${dark ? 'border-[#1e1e1e]' : 'border-gray-100'}`}>
                <span className={`text-[11px] font-semibold uppercase tracking-wider block mb-2 ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
                  Key Observations
                </span>
                <ul className="space-y-1.5">
                  {reasoning.key_observations.map((obs, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-brand text-xs mt-0.5 font-bold shrink-0">{i + 1}.</span>
                      <span className={`text-sm leading-relaxed ${dark ? 'text-gray-400' : 'text-gray-600'}`}>{obs}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Action plan */}
            {showObservations && suggestion && (
              <div className={`border-t pt-3 ${dark ? 'border-[#1e1e1e]' : 'border-gray-100'}`}>
                <span className={`text-[11px] font-semibold uppercase tracking-wider block mb-2 ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
                  Action Plan
                </span>
                <ul className="space-y-1.5">
                  {suggestion.action_plan.map((action, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-emerald-400 text-xs mt-0.5 shrink-0">&#x2022;</span>
                      <span className={`text-sm leading-relaxed ${dark ? 'text-gray-400' : 'text-gray-600'}`}>{action}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Recommended resources */}
            {showObservations && suggestion?.recommended_resources && suggestion.recommended_resources.length > 0 && (
              <div className={`border-t pt-3 ${dark ? 'border-[#1e1e1e]' : 'border-gray-100'}`}>
                <span className={`text-[11px] font-semibold uppercase tracking-wider block mb-2 ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
                  Recommended Resources
                </span>
                <ul className="space-y-1.5">
                  {suggestion.recommended_resources.map((res, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-blue-400 text-xs mt-0.5 shrink-0">&#x25B8;</span>
                      <span className={`text-sm leading-relaxed ${dark ? 'text-gray-400' : 'text-gray-600'}`}>{res}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <p className={`text-sm font-mono ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
            Awaiting next frame analysis...
          </p>
        )}
      </div>
    </div>
  )
}
