import { useState, useRef, useEffect } from 'react'
import { Sun, Moon, LogOut, Palette, Check } from 'lucide-react'
import { useTheme, type Theme } from '../context/ThemeContext'
import { useNavigate } from 'react-router-dom'

const THEME_OPTIONS: { key: Theme; label: string; icon: typeof Moon; desc: string }[] = [
  { key: 'dark', label: 'Dark', icon: Moon, desc: 'Default dark interface' },
  { key: 'light', label: 'Light', icon: Sun, desc: 'Clean light interface' },
  { key: 'verizon', label: 'Verizon', icon: Palette, desc: 'Verizon brand theme' },
]

export default function Header() {
  const { theme, setTheme } = useTheme()
  const navigate = useNavigate()
  const dark = theme === 'dark' || theme === 'verizon'
  const isVerizon = theme === 'verizon'

  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const currentIcon = theme === 'light' ? Sun : theme === 'verizon' ? Palette : Moon
  const CurrentIcon = currentIcon

  return (
    <header
      className={`flex items-center justify-between px-5 h-14 shrink-0 border-b ${
        isVerizon ? 'bg-vz-black border-vz-border' :
        dark ? 'bg-[#0e0e0e] border-[#1e1e1e]' : 'bg-white border-gray-200'
      }`}
    >
      <div className="flex items-center gap-3">
        <img
          src="/assets/logo.png"
          alt="Wildfire Watch"
          className={`h-9 w-9 object-contain ${dark ? '' : 'brightness-0'}`}
        />
        <div className="flex items-center gap-2">
          <span className={`text-base font-bold tracking-wide ${dark ? 'text-white' : 'text-gray-900'}`}>
            WILDFIRE WATCH
          </span>
          <span className={`text-base font-bold ${isVerizon ? 'text-vz-red' : 'text-brand'}`}>MVP</span>
        </div>
        {isVerizon && (
          <div className="flex items-center gap-1.5 ml-1">
            <span className="text-[10px] font-bold tracking-widest uppercase text-vz-red bg-vz-red/10 px-2 py-0.5 rounded">
              Verizon
            </span>
          </div>
        )}
        <div className="flex items-center gap-1.5 ml-3">
          <span className={`h-2 w-2 rounded-full animate-pulse ${isVerizon ? 'bg-vz-red' : 'bg-emerald-500'}`} />
          <span className={`text-xs uppercase tracking-wider ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
            System Operational
          </span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        {/* Theme selector */}
        <div className="relative" ref={ref}>
          <button
            onClick={() => setOpen(!open)}
            className={`flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm transition-colors cursor-pointer ${
              isVerizon ? 'bg-vz-dark text-gray-400 hover:text-white' :
              dark ? 'bg-[#1a1a1a] text-gray-400 hover:text-white' : 'bg-gray-100 text-gray-600 hover:text-gray-900'
            }`}
          >
            <CurrentIcon className="h-4 w-4" />
            {THEME_OPTIONS.find(t => t.key === theme)?.label}
          </button>

          {open && (
            <div className={`absolute right-0 top-full mt-1.5 w-52 rounded-xl border shadow-xl z-50 overflow-hidden ${
              dark ? 'bg-[#141414] border-[#2a2a2a]' : 'bg-white border-gray-200'
            }`}>
              {THEME_OPTIONS.map(opt => {
                const Icon = opt.icon
                const active = theme === opt.key
                return (
                  <button
                    key={opt.key}
                    onClick={() => { setTheme(opt.key); setOpen(false) }}
                    className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors cursor-pointer ${
                      active
                        ? isVerizon ? 'bg-vz-red/10' : 'bg-brand/10'
                        : dark ? 'hover:bg-[#1a1a1a]' : 'hover:bg-gray-50'
                    }`}
                  >
                    <div className={`h-8 w-8 rounded-lg flex items-center justify-center ${
                      opt.key === 'verizon' ? 'bg-vz-red/15' :
                      opt.key === 'dark' ? (dark ? 'bg-[#1a1a1a]' : 'bg-gray-100') :
                      'bg-amber-100'
                    }`}>
                      <Icon className={`h-4 w-4 ${
                        opt.key === 'verizon' ? 'text-vz-red' :
                        opt.key === 'dark' ? (dark ? 'text-gray-400' : 'text-gray-500') :
                        'text-amber-600'
                      }`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className={`text-xs font-semibold ${dark ? 'text-white' : 'text-gray-900'}`}>{opt.label}</p>
                      <p className={`text-[11px] ${dark ? 'text-gray-500' : 'text-gray-400'}`}>{opt.desc}</p>
                    </div>
                    {active && <Check className={`h-4 w-4 shrink-0 ${isVerizon ? 'text-vz-red' : 'text-brand'}`} />}
                  </button>
                )
              })}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2.5">
          <div className="text-right">
            <p className={`text-xs uppercase tracking-wider ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
              Battalion Chief
            </p>
            <p className={`text-sm font-medium ${dark ? 'text-white' : 'text-gray-900'}`}>
              Khoi Duong
            </p>
          </div>
          <div className={`flex h-9 w-9 items-center justify-center rounded-full text-white text-sm font-bold ${isVerizon ? 'bg-vz-red' : 'bg-brand'}`}>
            K
          </div>
        </div>

        <button
          onClick={() => navigate('/')}
          className={`p-2 rounded-lg transition-colors cursor-pointer ${
            dark ? 'text-gray-500 hover:text-white hover:bg-[#1a1a1a]' : 'text-gray-400 hover:text-gray-900 hover:bg-gray-100'
          }`}
        >
          <LogOut className="h-5 w-5" />
        </button>
      </div>
    </header>
  )
}
