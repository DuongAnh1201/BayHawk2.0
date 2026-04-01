import { Shield, Sun, Moon, LogOut } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import { useNavigate } from 'react-router-dom'

export default function Header() {
  const { theme, toggleTheme } = useTheme()
  const navigate = useNavigate()
  const dark = theme === 'dark'

  return (
    <header
      className={`flex items-center justify-between px-5 h-12 shrink-0 border-b ${
        dark ? 'bg-[#0e0e0e] border-[#1e1e1e]' : 'bg-white border-gray-200'
      }`}
    >
      <div className="flex items-center gap-3">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand">
          <Shield className="h-4 w-4 text-white" strokeWidth={2.5} />
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-sm font-bold tracking-wide ${dark ? 'text-white' : 'text-gray-900'}`}>
            WILDFIRE WATCH
          </span>
          <span className="text-sm font-bold text-brand">MVP</span>
        </div>
        <div className="flex items-center gap-1.5 ml-3">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className={`text-[10px] uppercase tracking-wider ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
            System Operational
          </span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button
          onClick={toggleTheme}
          className={`flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-xs transition-colors cursor-pointer ${
            dark
              ? 'bg-[#1a1a1a] text-gray-400 hover:text-white'
              : 'bg-gray-100 text-gray-600 hover:text-gray-900'
          }`}
        >
          {dark ? <Sun className="h-3.5 w-3.5" /> : <Moon className="h-3.5 w-3.5" />}
          {dark ? 'Light' : 'Dark'}
        </button>

        <div className="flex items-center gap-2.5">
          <div className="text-right">
            <p className={`text-[10px] uppercase tracking-wider ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
              Battalion Chief
            </p>
            <p className={`text-xs font-medium ${dark ? 'text-white' : 'text-gray-900'}`}>
              Khoi Duong
            </p>
          </div>
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand text-white text-xs font-bold">
            K
          </div>
        </div>

        <button
          onClick={() => navigate('/')}
          className={`p-1.5 rounded-lg transition-colors cursor-pointer ${
            dark ? 'text-gray-500 hover:text-white hover:bg-[#1a1a1a]' : 'text-gray-400 hover:text-gray-900 hover:bg-gray-100'
          }`}
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </header>
  )
}
