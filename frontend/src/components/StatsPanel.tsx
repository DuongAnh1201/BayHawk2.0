import { useState, useEffect } from 'react'
import { Radio, AlertTriangle, Zap, ChevronRight } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'

interface StatCard {
  icon: React.ReactNode
  label: string
  value: string
  color: string
}

export default function StatsPanel() {
  const { theme } = useTheme()
  const dark = theme === 'dark'
  const [latency, setLatency] = useState(1.2)

  useEffect(() => {
    const interval = setInterval(() => {
      setLatency(prev => {
        const jitter = (Math.random() - 0.5) * 0.4
        return Math.max(0.5, Math.min(3, prev + jitter))
      })
    }, 3000)
    return () => clearInterval(interval)
  }, [])

  const stats: StatCard[] = [
    {
      icon: <Radio className="h-4 w-4" />,
      label: 'Active Nodes',
      value: '2/4',
      color: 'text-blue-400',
    },
    {
      icon: <AlertTriangle className="h-4 w-4" />,
      label: 'Total Alerts',
      value: '0',
      color: 'text-amber-400',
    },
    {
      icon: <Zap className="h-4 w-4" />,
      label: 'Avg Latency',
      value: `${latency.toFixed(1)}s`,
      color: 'text-emerald-400',
    },
  ]

  return (
    <div className="grid grid-cols-3 gap-3">
      {stats.map(stat => (
        <div
          key={stat.label}
          className={`rounded-xl border px-4 py-3 flex items-center justify-between ${
            dark ? 'bg-[#111] border-[#1e1e1e]' : 'bg-white border-gray-200'
          }`}
        >
          <div className="flex items-center gap-3">
            <div className={`${stat.color}`}>{stat.icon}</div>
            <div>
              <p className={`text-[10px] uppercase tracking-wider ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
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
