import { useState, useCallback } from 'react'
import { LayoutGrid, Target, FileText, Crosshair } from 'lucide-react'
import { useTheme } from '../context/ThemeContext'
import { PipelineProvider, usePipeline } from '../context/PipelineContext'
import Header from '../components/Header'
import Sidebar from '../components/Sidebar'
import AlertBanner from '../components/AlertBanner'
import LiveIngestion from '../components/LiveIngestion'
import MultiCameraView from '../components/MultiCameraView'
import VisualReasoning from '../components/VisualReasoning'
import SpatialMonitoring from '../components/SpatialMonitoring'
import StatsPanel from '../components/StatsPanel'
import DronePanel from '../components/DronePanel'
import DroneSystemPanel from '../components/DroneSystemPanel'
import DeescalationTimeline from '../components/DeescalationTimeline'
import IncidentReport from '../components/IncidentReport'
import StatusBar from '../components/StatusBar'

type ViewMode = 'multi' | 'event' | 'drone' | 'report'

const TABS: { mode: ViewMode; label: string; icon: React.ReactNode; subtitle: string }[] = [
  { mode: 'multi', label: 'Multi-Camera', icon: <LayoutGrid className="h-4 w-4" />, subtitle: 'Surveillance Overview' },
  { mode: 'event', label: 'Main Event', icon: <Target className="h-4 w-4" />, subtitle: 'Incident Focus' },
  { mode: 'drone', label: 'Drone System', icon: <Crosshair className="h-4 w-4" />, subtitle: 'Drone Command & Fleet' },
  { mode: 'report', label: 'Report', icon: <FileText className="h-4 w-4" />, subtitle: 'Incident Report' },
]

function DashboardContent() {
  const { theme } = useTheme()
  const dark = theme === 'dark' || theme === 'verizon'
  const { setSelectedCamera } = usePipeline()

  const [viewMode, setViewMode] = useState<ViewMode>('multi')

  const handleFocusCamera = useCallback((id: string) => {
    setSelectedCamera(id)
    setViewMode('event')
  }, [setSelectedCamera])

  const currentTab = TABS.find(t => t.mode === viewMode)!

  return (
    <div className={`flex flex-col h-full ${dark ? 'bg-[#080808]' : 'bg-gray-100'}`}>
      <AlertBanner />
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-4 space-y-3">
          {/* Mode toggle bar */}
          <div className="flex items-center justify-between">
            <div className={`inline-flex rounded-lg p-0.5 ${dark ? 'bg-[#1a1a1a]' : 'bg-gray-200'}`}>
              {TABS.map(tab => (
                <button
                  key={tab.mode}
                  onClick={() => setViewMode(tab.mode)}
                  className={`flex items-center gap-2 rounded-md px-4 py-2 text-sm font-medium transition-colors cursor-pointer ${
                    viewMode === tab.mode
                      ? 'bg-brand text-white shadow-sm'
                      : dark ? 'text-gray-400 hover:text-white' : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  {tab.icon}
                  {tab.label}
                </button>
              ))}
            </div>

            <span className={`text-xs uppercase tracking-wider ${dark ? 'text-gray-600' : 'text-gray-400'}`}>
              {currentTab.subtitle}
            </span>
          </div>

          {viewMode === 'multi' && (
            <>
              <div className="h-[calc(100vh-260px)] min-h-[400px]">
                <MultiCameraView onFocusCamera={handleFocusCamera} />
              </div>
              <StatsPanel />
            </>
          )}

          {viewMode === 'event' && (
            <>
              <div className="grid grid-cols-5 gap-3">
                <div className="col-span-3 h-[400px]">
                  <LiveIngestion />
                </div>
                <div className="col-span-2 h-[400px]">
                  <SpatialMonitoring />
                </div>
              </div>
              <div className="grid grid-cols-5 gap-3">
                <div className="col-span-3">
                  <VisualReasoning />
                </div>
                <div className="col-span-2 space-y-3">
                  <DronePanel />
                  <DeescalationTimeline />
                </div>
              </div>
              <StatsPanel />
            </>
          )}

          {viewMode === 'drone' && (
            <div className="h-[calc(100vh-220px)] min-h-[500px]">
              <DroneSystemPanel />
            </div>
          )}

          {viewMode === 'report' && (
            <IncidentReport />
          )}
        </main>
      </div>

      <StatusBar />
    </div>
  )
}

export default function Dashboard() {
  return (
    <PipelineProvider>
      <DashboardContent />
    </PipelineProvider>
  )
}
