import { useNavigate } from 'react-router-dom'
import { User } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'

export default function Login() {
  const navigate = useNavigate()
  const { theme } = useTheme()
  const dark = theme === 'dark' || theme === 'verizon'
  const isVerizon = theme === 'verizon'

  const handleSignIn = () => {
    navigate('/dashboard')
  }

  return (
    <div
      className={`flex items-center justify-center h-full ${
        isVerizon ? 'bg-vz-black' : dark ? 'bg-[#080808]' : 'bg-gray-100'
      }`}
    >
      <div
        className={`w-[420px] rounded-2xl p-12 text-center shadow-2xl border ${
          isVerizon
            ? 'bg-vz-card border-vz-border'
            : dark
              ? 'bg-[#141414] border-[#2a2a2a]'
              : 'bg-white border-gray-200'
        }`}
      >
        <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center">
          <img
            src="/assets/logo.png"
            alt="Wildfire Watch"
            className={`h-20 w-20 object-contain ${dark ? 'invert' : ''}`}
          />
        </div>

        {isVerizon && (
          <div className="mb-4">
            <span className="text-[10px] font-bold tracking-[0.3em] uppercase text-vz-red bg-vz-red/10 px-3 py-1 rounded-full">
              Powered by Verizon
            </span>
          </div>
        )}

        <h1
          className={`text-2xl font-semibold mb-1 ${
            dark ? 'text-white' : 'text-gray-900'
          }`}
        >
          Wildfire Watch MVP
        </h1>
        <p
          className={`text-base mb-8 ${
            dark ? 'text-gray-400' : 'text-gray-500'
          }`}
        >
          Battalion Chief Command Center Access
        </p>

        <button
          onClick={handleSignIn}
          className={`w-full flex items-center justify-center gap-2.5 rounded-lg px-4 py-3.5 text-base font-medium transition-colors cursor-pointer ${
            isVerizon
              ? 'bg-vz-red text-white hover:bg-vz-red-light'
              : dark
                ? 'bg-white text-gray-900 hover:bg-gray-100'
                : 'bg-gray-900 text-white hover:bg-gray-800'
          }`}
        >
          <User className="h-5 w-5" />
          Sign in with Google
        </button>

        <p
          className={`mt-8 text-xs font-medium tracking-[0.2em] uppercase ${
            dark ? 'text-gray-600' : 'text-gray-400'
          }`}
        >
          Authorized Personnel Only
        </p>
      </div>
    </div>
  )
}
