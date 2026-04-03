import { Crosshair, Rocket, CheckCircle, Navigation, Droplets, Wind } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import { usePipeline } from '../context/PipelineContext'

const STATUS_LABELS: Record<string, { label: string; color: string; icon: typeof Rocket }> = {
  launching: { label: 'Launching', color: 'text-amber-400', icon: Rocket },
  'en-route': { label: 'En Route', color: 'text-blue-400', icon: Navigation },
  dropping: { label: 'Dropping Payload', color: 'text-red-400', icon: Droplets },
  returning: { label: 'Returning', color: 'text-purple-400', icon: Wind },
  complete: { label: 'Complete', color: 'text-emerald-400', icon: CheckCircle },
}

export default function DronePanel() {
  const { theme } = useTheme()
  const dark = theme === 'dark' || theme === 'verizon'
  const {
    droneStations,
    droneDispatches,
    pipelineResult,
    activeScenario,
  } = usePipeline()

  const criticality = pipelineResult?.classification?.criticality
  const showPanel = activeScenario === 'fire_high' || activeScenario === 'critical' || criticality === 'HIGH' || criticality === 'CRITICAL'

  const activeDispatches = droneDispatches.filter(d => d.status !== 'complete')
  const completedDispatches = droneDispatches.filter(d => d.status === 'complete')
  const totalDrones = droneStations.reduce((a, s) => a + s.dronesTotal, 0)
  const availDrones = droneStations.reduce((a, s) => a + s.drones, 0)

  return (
    <div className={`rounded-xl border overflow-hidden ${dark ? 'bg-[#111] border-[#1e1e1e]' : 'bg-white border-gray-200'}`}>
      <div className={`flex items-center justify-between px-4 py-2.5 border-b ${dark ? 'border-[#1e1e1e]' : 'border-gray-100'}`}>
        <div className="flex items-center gap-2">
          <Crosshair className={`h-4 w-4 ${showPanel ? 'text-emerald-400' : dark ? 'text-gray-500' : 'text-gray-400'}`} />
          <span className={`text-sm font-semibold uppercase tracking-wider ${dark ? 'text-gray-400' : 'text-gray-600'}`}>
            Drone Response
          </span>
          {activeDispatches.length > 0 && (
            <span className="text-xs font-bold text-amber-400 bg-amber-400/10 rounded px-2 py-0.5 animate-pulse">
              {activeDispatches.length} active
            </span>
          )}
        </div>
        <span className={`text-xs ${dark ? 'text-gray-600' : 'text-gray-400'}`}>
          {availDrones}/{totalDrones} drones
        </span>
      </div>

      <div className="p-3 space-y-2">
        {/* Quick fleet status */}
        <div className="grid grid-cols-3 gap-1.5">
          {droneStations.map(ds => (
            <div key={ds.id} className={`rounded-lg p-2 text-center ${dark ? 'bg-[#1a1a1a]' : 'bg-gray-50'}`}>
              <p className={`text-[10px] font-medium truncate ${dark ? 'text-gray-500' : 'text-gray-400'}`}>{ds.code}</p>
              <p className={`text-sm font-bold ${ds.drones === ds.dronesTotal ? (dark ? 'text-emerald-400' : 'text-emerald-600') : ds.drones > 0 ? 'text-amber-400' : 'text-red-400'}`}>
                {ds.drones}/{ds.dronesTotal}
              </p>
              <span className={`h-1.5 w-1.5 rounded-full inline-block ${ds.status === 'ready' ? 'bg-emerald-500' : 'bg-red-400 animate-pulse'}`} />
            </div>
          ))}
        </div>

        {/* Active missions */}
        {activeDispatches.length > 0 && (
          <div className="flex flex-col gap-1">
            {activeDispatches.map((d, i) => {
              const info = STATUS_LABELS[d.status]
              const stationData = droneStations.find(s => s.id === d.stationId)
              const StatusIcon = info?.icon ?? Rocket
              return (
                <div key={i} className={`flex items-center justify-between rounded-lg px-2.5 py-1.5 ${dark ? 'bg-[#1a1a1a]' : 'bg-gray-50'}`}>
                  <div className="flex items-center gap-1.5">
                    <StatusIcon className={`h-3.5 w-3.5 ${info?.color ?? 'text-gray-400'} animate-pulse`} />
                    <span className={`text-[11px] ${dark ? 'text-gray-400' : 'text-gray-600'}`}>{stationData?.code}</span>
                    <span className={`text-[11px] font-medium ${dark ? 'text-gray-300' : 'text-gray-700'}`}>{d.payload}</span>
                  </div>
                  <span className={`text-[11px] font-semibold ${info?.color ?? 'text-gray-400'}`}>{info?.label}</span>
                </div>
              )
            })}
          </div>
        )}

        {completedDispatches.length > 0 && (
          <div className={`text-xs ${dark ? 'text-gray-600' : 'text-gray-400'} flex items-center gap-1`}>
            <CheckCircle className="h-3 w-3 text-emerald-500" />
            {completedDispatches.length} mission{completedDispatches.length > 1 ? 's' : ''} completed
          </div>
        )}

        {!showPanel && activeDispatches.length === 0 && (
          <p className={`text-xs text-center py-2 ${dark ? 'text-gray-600' : 'text-gray-400'}`}>
            Standby — No Active Threats
          </p>
        )}

        <p className={`text-[10px] text-center ${dark ? 'text-gray-700' : 'text-gray-300'}`}>
          Switch to Drone System tab for full controls
        </p>
      </div>
    </div>
  )
}
