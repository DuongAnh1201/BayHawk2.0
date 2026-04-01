import { useTheme } from '../context/ThemeContext'
import Header from '../components/Header'
import Sidebar from '../components/Sidebar'
import LiveIngestion from '../components/LiveIngestion'
import VisualReasoning from '../components/VisualReasoning'
import SpatialMonitoring from '../components/SpatialMonitoring'
import StatsPanel from '../components/StatsPanel'
import StatusBar from '../components/StatusBar'

export default function Dashboard() {
  const { theme } = useTheme()
  const dark = theme === 'dark'

  return (
    <div className={`flex flex-col h-full ${dark ? 'bg-[#080808]' : 'bg-gray-100'}`}>
      <Header />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar />

        <main className="flex-1 overflow-y-auto p-4 flex flex-col gap-3">
          {/* Top row: ingestion + map */}
          <div className="grid grid-cols-5 gap-3 flex-1 min-h-0">
            <div className="col-span-3 flex flex-col gap-3">
              <div className="flex-1 min-h-0">
                <LiveIngestion />
              </div>
              <VisualReasoning />
            </div>
            <div className="col-span-2">
              <SpatialMonitoring />
            </div>
          </div>

          {/* Stats row */}
          <StatsPanel />
        </main>
      </div>

      <StatusBar />
    </div>
  )
}
