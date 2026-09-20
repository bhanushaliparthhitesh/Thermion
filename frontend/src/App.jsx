import { Routes, Route } from 'react-router-dom'
import { RoleProvider } from './context/RoleContext'
import AppShell from './components/layout/AppShell'

import CommandCenter from './pages/CommandCenter'
import DigitalTwin from './pages/DigitalTwin'
import AIDecisions from './pages/AIDecisions'
import SafetyCenter from './pages/SafetyCenter'
import LiveTelemetry from './pages/LiveTelemetry'
import Analytics from './pages/Analytics'
import Alerts from './pages/Alerts'
import AskThermion from './pages/AskThermion'

export default function App() {
  return (
    <RoleProvider>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<CommandCenter />} />
          <Route path="digital-twin" element={<DigitalTwin />} />
          <Route path="decisions" element={<AIDecisions />} />
          <Route path="decisions/:stepId" element={<AIDecisions />} />
          <Route path="safety" element={<SafetyCenter />} />
          <Route path="telemetry" element={<LiveTelemetry />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="ask" element={<AskThermion />} />
        </Route>
      </Routes>
    </RoleProvider>
  )
}
