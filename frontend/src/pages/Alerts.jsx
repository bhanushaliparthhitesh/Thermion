import PageStub from '../components/common/PageStub'

export default function Alerts() {
  return (
    <PageStub
      title="Alerts"
      subtitle="System notifications and safety events"
      needs={[
        'Severity classification is not logged today (Safety Center already surfaces the raw interventions)',
        'A dedicated alerts store, or a derivation rule from decision history (e.g. three consecutive high-risk steps = warning)',
      ]}
    />
  )
}
