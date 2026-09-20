import PageStub from '../components/common/PageStub'

export default function LiveTelemetry() {
  return (
    <PageStub
      title="Live Telemetry"
      subtitle="Real-time and historical sensor readings"
      needs={[
        'Nothing new on the backend — this is buildable now from GET /decisions history',
        'A charting library wired in (recharts is a good fit alongside the existing stack)',
        'Time-range filters (5 min / 15 min / 1 hr / 6 hr / 24 hr) — need enough history logged to be meaningful',
      ]}
    />
  )
}
