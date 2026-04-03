import { Wind, Droplets, Compass, Flame } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import { usePipeline } from '../context/PipelineContext'

function windDirLabel(deg: number): string {
  const dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
  return dirs[Math.round(deg / 45) % 8]
}

function riskColor(risk: number): string {
  if (risk >= 0.75) return 'text-red-400'
  if (risk >= 0.5) return 'text-amber-400'
  if (risk >= 0.25) return 'text-yellow-400'
  return 'text-emerald-400'
}

function riskLabel(risk: number): string {
  if (risk >= 0.75) return 'CRITICAL'
  if (risk >= 0.5) return 'HIGH'
  if (risk >= 0.25) return 'MODERATE'
  return 'LOW'
}

export default function WeatherPanel() {
  const { theme } = useTheme()
  const { pipelineResult } = usePipeline()
  const dark = theme === 'dark' || theme === 'verizon'
  const w = pipelineResult?.weather

  const items = [
    {
      icon: <Wind className="h-4 w-4" />,
      label: 'Wind',
      value: w ? `${w.wind_speed.toFixed(1)} m/s` : '—',
      sub: w ? windDirLabel(w.wind_direction) : '',
    },
    {
      icon: <Droplets className="h-4 w-4" />,
      label: 'Humidity',
      value: w ? `${w.humidity.toFixed(0)}%` : '—',
      sub: '',
    },
    {
      icon: <Compass className="h-4 w-4" />,
      label: 'Direction',
      value: w ? `${w.wind_direction.toFixed(0)}°` : '—',
      sub: w ? windDirLabel(w.wind_direction) : '',
    },
    {
      icon: <Flame className="h-4 w-4" />,
      label: 'Spread Risk',
      value: w ? riskLabel(w.spread_risk) : '—',
      sub: w ? `${(w.spread_risk * 100).toFixed(0)}%` : '',
      valueClass: w ? riskColor(w.spread_risk) : '',
    },
  ]

  return (
    <div className={`p-4 border-t ${dark ? 'border-[#1e1e1e]' : 'border-gray-200'}`}>
      <span
        className={`text-xs font-semibold uppercase tracking-wider block mb-3 ${
          dark ? 'text-gray-500' : 'text-gray-400'
        }`}
      >
        Weather Intel
      </span>

      <div className="grid grid-cols-2 gap-2">
        {items.map(item => (
          <div
            key={item.label}
            className={`rounded-lg p-2.5 ${dark ? 'bg-[#141414]' : 'bg-gray-100'}`}
          >
            <div className="flex items-center gap-1.5 mb-1">
              <span className={dark ? 'text-gray-600' : 'text-gray-400'}>{item.icon}</span>
              <span className={`text-[11px] uppercase tracking-wider ${dark ? 'text-gray-600' : 'text-gray-400'}`}>
                {item.label}
              </span>
            </div>
            <p className={`text-base font-bold leading-tight ${'valueClass' in item && item.valueClass ? item.valueClass : dark ? 'text-white' : 'text-gray-900'}`}>
              {item.value}
            </p>
            {item.sub && (
              <p className={`text-xs ${dark ? 'text-gray-600' : 'text-gray-400'}`}>{item.sub}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
