import { useState } from 'react'
import { X, Send, CheckCircle, AlertCircle, Users, Radio, MapPin } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import { usePipeline } from '../context/PipelineContext'
import { sendSMSAlert } from '../services/sms'

interface RecipientGroup {
  id: string
  label: string
  description: string
  icon: React.ReactNode
  contacts: string[]
}

const ALL_GROUPS: RecipientGroup[] = [
  {
    id: 'firefighters',
    label: 'On-Duty Firefighters',
    description: 'Active duty fire crews and engine companies',
    icon: <Users className="h-5 w-5" />,
    contacts: ['+1 (555) 100-0001', '+1 (555) 100-0002', '+1 (555) 100-0003'],
  },
  {
    id: 'control_center',
    label: 'Control Center',
    description: 'Dispatch, operations, and command staff',
    icon: <Radio className="h-5 w-5" />,
    contacts: ['+1 (555) 200-0001', '+1 (555) 200-0002'],
  },
  {
    id: 'area_residents',
    label: 'Area Residents',
    description: 'Registered residents within evacuation radius',
    icon: <MapPin className="h-5 w-5" />,
    contacts: ['+1 (555) 300-****  (147 contacts)'],
  },
]

type SendStatus = 'idle' | 'sending' | 'sent' | 'error'

interface Props {
  onClose: () => void
  residentsOnly?: boolean
}

export default function SMSPanel({ onClose, residentsOnly }: Props) {
  const { theme } = useTheme()
  const dark = theme === 'dark' || theme === 'verizon'
  const { pipelineResult, cameras, selectedCamera } = usePipeline()

  const groups = residentsOnly
    ? ALL_GROUPS.filter(g => g.id === 'area_residents')
    : ALL_GROUPS

  const [selected, setSelected] = useState<Set<string>>(
    new Set(residentsOnly ? ['area_residents'] : ['firefighters', 'control_center']),
  )
  const [status, setStatus] = useState<SendStatus>('idle')
  const [errorMsg, setErrorMsg] = useState('')

  const classification = pipelineResult?.classification
  const suggestion = pipelineResult?.suggestion
  const cam = cameras.find(c => c.id === selectedCamera)

  const alertMessage = suggestion?.alert_message
    ?? `WILDFIRE ALERT — ${classification?.criticality ?? 'UNKNOWN'} criticality detected at ${cam?.name ?? 'Unknown location'}.`

  const toggle = (id: string) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const handleSend = async () => {
    if (selected.size === 0) return
    setStatus('sending')
    setErrorMsg('')

    try {
      await sendSMSAlert({
        groups: Array.from(selected),
        message: alertMessage,
        camera_name: cam?.name ?? 'Unknown',
        criticality: classification?.criticality ?? 'UNKNOWN',
        lat: cam?.lat,
        lon: cam?.lon,
      })
      setStatus('sent')
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to send SMS')
      setStatus('error')
    }
  }

  return (
    <div className="fixed inset-0 z-[10000] flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <div
        onClick={e => e.stopPropagation()}
        className={`w-[520px] max-h-[90vh] rounded-2xl shadow-2xl border overflow-hidden flex flex-col ${
          dark ? 'bg-[#141414] border-[#2a2a2a]' : 'bg-white border-gray-200'
        }`}
      >
        {/* Header */}
        <div className={`flex items-center justify-between px-6 py-4 border-b ${dark ? 'border-[#2a2a2a]' : 'border-gray-200'}`}>
          <div>
            <h2 className={`text-lg font-bold ${dark ? 'text-white' : 'text-gray-900'}`}>
              {residentsOnly ? 'Evacuation Alert — Area Residents' : 'Emergency SMS Alert'}
            </h2>
            <p className={`text-sm ${dark ? 'text-gray-400' : 'text-gray-500'}`}>
              {residentsOnly ? 'Send evacuation notice to registered residents' : 'Select recipient groups to notify'}
            </p>
          </div>
          <button
            onClick={onClose}
            className={`p-2 rounded-lg transition-colors cursor-pointer ${
              dark ? 'hover:bg-[#222] text-gray-400' : 'hover:bg-gray-100 text-gray-500'
            }`}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          <div className="space-y-2">
            {groups.map(group => (
              <button
                key={group.id}
                onClick={() => toggle(group.id)}
                className={`w-full flex items-center gap-4 rounded-xl p-4 text-left transition-colors cursor-pointer border ${
                  selected.has(group.id)
                    ? dark ? 'bg-red-500/10 border-red-500/30' : 'bg-red-50 border-red-200'
                    : dark ? 'bg-[#1a1a1a] border-transparent hover:bg-[#222]' : 'bg-gray-50 border-transparent hover:bg-gray-100'
                }`}
              >
                <div className={`shrink-0 flex items-center justify-center h-10 w-10 rounded-lg ${
                  selected.has(group.id)
                    ? 'bg-red-500 text-white'
                    : dark ? 'bg-[#222] text-gray-400' : 'bg-gray-200 text-gray-500'
                }`}>
                  {group.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm font-semibold ${dark ? 'text-white' : 'text-gray-900'}`}>
                    {group.label}
                  </p>
                  <p className={`text-xs ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
                    {group.description}
                  </p>
                  <p className={`text-xs font-mono mt-1 ${dark ? 'text-gray-600' : 'text-gray-400'}`}>
                    {group.contacts.join(' · ')}
                  </p>
                </div>
                <div className={`h-5 w-5 rounded-md border-2 flex items-center justify-center shrink-0 ${
                  selected.has(group.id)
                    ? 'bg-red-500 border-red-500'
                    : dark ? 'border-gray-600' : 'border-gray-300'
                }`}>
                  {selected.has(group.id) && (
                    <svg className="h-3 w-3 text-white" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M2 6l3 3 5-5" />
                    </svg>
                  )}
                </div>
              </button>
            ))}
          </div>

          {/* Message preview */}
          <div>
            <span className={`text-xs font-semibold uppercase tracking-wider block mb-2 ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
              Message Preview
            </span>
            <div className={`rounded-xl p-4 border text-sm leading-relaxed ${
              dark ? 'bg-[#1a1a1a] border-[#2a2a2a] text-gray-300' : 'bg-gray-50 border-gray-200 text-gray-700'
            }`}>
              {alertMessage}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className={`px-6 py-4 border-t ${dark ? 'border-[#2a2a2a]' : 'border-gray-200'}`}>
          {status === 'sent' ? (
            <div className="flex items-center gap-2 text-emerald-400">
              <CheckCircle className="h-5 w-5" />
              <span className="text-sm font-semibold">
                {residentsOnly ? 'Evacuation SMS sent to area residents' : `SMS alerts sent successfully to ${selected.size} group${selected.size > 1 ? 's' : ''}`}
              </span>
            </div>
          ) : status === 'error' ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-red-400">
                <AlertCircle className="h-5 w-5" />
                <span className="text-sm font-semibold">{errorMsg}</span>
              </div>
              <button
                onClick={handleSend}
                className="w-full flex items-center justify-center gap-2 rounded-lg bg-red-500 hover:bg-red-600 px-4 py-3 text-sm font-semibold text-white transition-colors cursor-pointer"
              >
                <Send className="h-4 w-4" />
                Retry Send
              </button>
            </div>
          ) : (
            <button
              onClick={handleSend}
              disabled={selected.size === 0 || status === 'sending'}
              className="w-full flex items-center justify-center gap-2 rounded-lg bg-red-500 hover:bg-red-600 disabled:opacity-50 px-4 py-3 text-sm font-semibold text-white transition-colors cursor-pointer"
            >
              {status === 'sending' ? (
                <>
                  <span className="inline-block h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Sending...
                </>
              ) : (
                <>
                  <Send className="h-4 w-4" />
                  {residentsOnly ? 'Send Evacuation Alert to Residents' : `Send Alert to ${selected.size} Group${selected.size !== 1 ? 's' : ''}`}
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
