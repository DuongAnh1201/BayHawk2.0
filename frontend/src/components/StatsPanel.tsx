import { Radio, AlertTriangle, Zap, Wind, Droplets, ChevronRight } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import { usePipeline } from '../context/PipelineContext'

export default function StatsPanel() {
  const { theme } = useTheme()
  const dark = theme === 'dark' || theme === 'verizon'
  const { cameras, pipelineResult } = usePipeline()

  const onlineCount = cameras.filter(c => c.online).length
  const weather = pipelineResult?.weather
  const classification = pipelineResult?.classification
  const alertCount = classification ? 1 : 0

  const totalLatency =
    (pipelineResult?.camera?.latency_ms ?? 0) +
    (pipelineResult?.satellite?.latency_ms ?? 0) +
    (pipelineResult?.weather?.latency_ms ?? 0)
  const avgLatency = pipelineResult ? totalLatency / 3 : 0

  const stats = [
    {
      icon: <Radio className="h-5 w-5" />,
      label: 'Active Nodes',
      value: `${onlineCount}/${cameras.length}`,
      color: 'text-blue-400',
    },
    {
      icon: <AlertTriangle className="h-5 w-5" />,
      label: 'Total Alerts',
      value: String(alertCount),
      color: alertCount > 0 ? 'text-red-400' : 'text-amber-400',
    },
    {
      icon: <Zap className="h-5 w-5" />,
      label: 'Avg Latency',
      value: pipelineResult ? `${(avgLatency / 1000).toFixed(1)}s` : '—',
      color: 'text-emerald-400',
    },
    {
      icon: <Wind className="h-5 w-5" />,
      label: 'Wind Speed',
      value: weather ? `${weather.wind_speed.toFixed(1)} m/s` : '—',
      color: 'text-cyan-400',
    },
    {
      icon: <Droplets className="h-5 w-5" />,
      label: 'Humidity',
      value: weather ? `${weather.humidity.toFixed(0)}%` : '—',
      color: weather && weather.humidity < 25 ? 'text-red-400' : 'text-sky-400',
    },
  ]

  return (
    <div className="grid grid-cols-5 gap-3">
      {stats.map(stat => (
        <div
          key={stat.label}
          className={`rounded-xl border px-4 py-3.5 flex items-center justify-between ${
            dark ? 'bg-[#111] border-[#1e1e1e]' : 'bg-white border-gray-200'
          }`}
        >
          <div className="flex items-center gap-3">
            <div className={stat.color}>{stat.icon}</div>
            <div>
              <p className={`text-xs uppercase tracking-wider ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
                {stat.label}
              </p>
              <p className={`text-xl font-bold ${dark ? 'text-white' : 'text-gray-900'}`}>
                {stat.value}
              </p>
            </div>
          </div>
          <ChevronRight className={`h-4 w-4 ${dark ? 'text-gray-700' : 'text-gray-300'}`} />
        </div>
      ))}
    </div>
  )
}
