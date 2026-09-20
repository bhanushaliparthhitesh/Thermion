import PageStub from '../components/common/PageStub'

export default function Analytics() {
  return (
    <PageStub
      title="Performance Analytics"
      subtitle="Energy, water, and efficiency trends for managers"
      needs={[
        'An energy-consumption metric — not currently in opensearch_schema.json or the state dict',
        'A defined baseline to compute "savings" against (per the no-fake-numbers rule, this can\'t be estimated)',
        'Cooling mode distribution is derivable today from action_label across decisions',
      ]}
    />
  )
}
