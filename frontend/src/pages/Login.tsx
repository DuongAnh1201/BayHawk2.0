import { useNavigate } from 'react-router-dom'
import { Shield, User } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'

export default function Login() {
  const navigate = useNavigate()
  const { theme } = useTheme()

  const handleSignIn = () => {
    navigate('/dashboard')
  }

  return (
    <div
      className={`flex items-center justify-center h-full ${
        theme === 'dark' ? 'bg-[#080808]' : 'bg-gray-100'
      }`}
    >
      <div
        className={`w-[380px] rounded-2xl p-10 text-center shadow-2xl border ${
          theme === 'dark'
            ? 'bg-[#141414] border-[#2a2a2a]'
            : 'bg-white border-gray-200'
        }`}
      >
        <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-xl bg-brand">
          <Shield className="h-7 w-7 text-white" strokeWidth={2.5} />
        </div>

        <h1
          className={`text-xl font-semibold mb-1 ${
            theme === 'dark' ? 'text-white' : 'text-gray-900'
          }`}
        >
          Wildfire Watch MVP
        </h1>
        <p
          className={`text-sm mb-8 ${
            theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
          }`}
        >
          Battalion Chief Command Center Access
        </p>

        <button
          onClick={handleSignIn}
          className={`w-full flex items-center justify-center gap-2.5 rounded-lg px-4 py-3 text-sm font-medium transition-colors cursor-pointer ${
            theme === 'dark'
              ? 'bg-white text-gray-900 hover:bg-gray-100'
              : 'bg-gray-900 text-white hover:bg-gray-800'
          }`}
        >
          <User className="h-4 w-4" />
          Sign in with Google
        </button>

        <p
          className={`mt-8 text-[10px] font-medium tracking-[0.2em] uppercase ${
            theme === 'dark' ? 'text-gray-600' : 'text-gray-400'
          }`}
        >
          Authorized Personnel Only
        </p>
      </div>
    </div>
  )
}
