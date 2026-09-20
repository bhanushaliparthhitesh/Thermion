import PageStub from '../components/common/PageStub'

export default function DigitalTwin() {
  return (
    <PageStub
      title="Digital Twin"
      subtitle="Real-time visualization of the data center cooling environment"
      needs={[
        'Per-rack telemetry from the backend (current schema only logs one system-wide state per decision)',
        'A Three.js scene (physical/thermal/airflow/cooling layers, orbit controls)',
        'A 2D fallback for environments without WebGL',
      ]}
    />
  )
}
