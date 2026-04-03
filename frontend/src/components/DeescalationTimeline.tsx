import { ShieldCheck, Flame, Droplets, Shrink, CheckCircle2 } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import { usePipeline, DEESCALATION_LABELS, type DeescalationPhase } from '../context/PipelineContext'

const PHASES: { key: DeescalationPhase; icon: typeof Flame }[] = [
  { key: 'responding', icon: Droplets },
  { key: 'containment', icon: Shrink },
  { key: 'controlled', icon: ShieldCheck },
  { key: 'extinguished', icon: CheckCircle2 },
]

function phaseIndex(phase: DeescalationPhase | null): number {
  if (!phase) return -1
  return PHASES.findIndex(p => p.key === phase)
}

export default function DeescalationTimeline() {
  const { theme } = useTheme()
  const dark = theme === 'dark' || theme === 'verizon'
  const { deescalationPhase, isDeescalating, startDeescalation, activeScenario } = usePipeline()

  const canStart = !isDeescalating && (activeScenario === 'fire_high' || activeScenario === 'critical')
  const currentIdx = phaseIndex(deescalationPhase)

  if (!canStart && !isDeescalating) return null

  return (
    <div className={`rounded-xl border overflow-hidden ${dark ? 'bg-[#111] border-[#1e1e1e]' : 'bg-white border-gray-200'}`}>
      <div className={`flex items-center justify-between px-4 py-2.5 border-b ${dark ? 'border-[#1e1e1e]' : 'border-gray-100'}`}>
        <div className="flex items-center gap-2">
          <Flame className={`h-4 w-4 ${isDeescalating ? 'text-amber-400 animate-pulse' : dark ? 'text-gray-500' : 'text-gray-400'}`} />
          <span className={`text-sm font-semibold uppercase tracking-wider ${dark ? 'text-gray-400' : 'text-gray-600'}`}>
            De-escalation Simulation
          </span>
        </div>
        {deescalationPhase && (
          <span className={`text-xs font-bold px-2 py-0.5 rounded ${DEESCALATION_LABELS[deescalationPhase].color} bg-current/10`}
            style={{ backgroundColor: 'transparent' }}
          >
            <span className={DEESCALATION_LABELS[deescalationPhase].color}>
              {DEESCALATION_LABELS[deescalationPhase].label}
            </span>
          </span>
        )}
      </div>

      <div className="p-4 space-y-4">
        {/* Start button */}
        {canStart && (
          <button
            onClick={startDeescalation}
            className="w-full flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-amber-600 to-emerald-600 hover:from-amber-500 hover:to-emerald-500 px-4 py-3 text-sm font-bold uppercase tracking-wider text-white transition-all cursor-pointer shadow-lg"
          >
            <ShieldCheck className="h-5 w-5" />
            Simulate De-escalation
          </button>
        )}

        {/* Phase timeline */}
        {isDeescalating && (
          <div className="relative">
            {PHASES.map((phase, i) => {
              const info = DEESCALATION_LABELS[phase.key]
              const Icon = phase.icon
              const isActive = i === currentIdx
              const isDone = i < currentIdx
              const isPending = i > currentIdx

              return (
                <div key={phase.key} className="flex items-start gap-3 relative">
                  {/* Vertical line */}
                  {i < PHASES.length - 1 && (
                    <div className={`absolute left-[15px] top-[32px] w-0.5 h-[calc(100%-8px)] ${
                      isDone ? 'bg-emerald-500' : dark ? 'bg-[#2a2a2a]' : 'bg-gray-200'
                    }`} />
                  )}

                  {/* Icon circle */}
                  <div className={`relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2 transition-all ${
                    isActive
                      ? `border-current ${info.color} bg-current/10 animate-pulse`
                      : isDone
                        ? 'border-emerald-500 bg-emerald-500/20'
                        : dark ? 'border-[#2a2a2a] bg-[#1a1a1a]' : 'border-gray-200 bg-gray-50'
                  }`}
                  style={isActive ? { borderColor: 'currentColor' } : {}}
                  >
                    <Icon className={`h-4 w-4 ${
                      isActive ? info.color : isDone ? 'text-emerald-400' : dark ? 'text-gray-600' : 'text-gray-400'
                    }`} />
                  </div>

                  {/* Content */}
                  <div className={`pb-5 flex-1 min-w-0 ${isPending ? 'opacity-40' : ''}`}>
                    <p className={`text-xs font-bold uppercase tracking-wider ${
                      isActive ? info.color : isDone ? 'text-emerald-400' : dark ? 'text-gray-500' : 'text-gray-400'
                    }`}>
                      {info.label}
                      {isActive && <span className="ml-2 normal-case font-normal animate-pulse">●</span>}
                      {isDone && <span className="ml-2 normal-case font-normal">✓</span>}
                    </p>
                    <p className={`text-[11px] mt-0.5 leading-relaxed ${dark ? 'text-gray-500' : 'text-gray-500'}`}>
                      {info.description}
                    </p>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Completion summary */}
        {deescalationPhase === 'extinguished' && (
          <div className={`rounded-lg p-3 border ${dark ? 'bg-emerald-500/5 border-emerald-500/20' : 'bg-emerald-50 border-emerald-200'}`}>
            <div className="flex items-center gap-2 mb-1">
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">
                Mission Accomplished
              </span>
            </div>
            <p className={`text-[11px] leading-relaxed ${dark ? 'text-gray-400' : 'text-gray-600'}`}>
              Fire successfully extinguished through coordinated drone and ground operations. All personnel safe. Returning to routine monitoring.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
