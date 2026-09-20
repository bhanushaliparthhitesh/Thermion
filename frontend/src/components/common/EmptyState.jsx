export default function EmptyState({ title = 'No data yet', hint, action }) {
  return (
    <div className="flex flex-col items-start gap-2 py-8 text-sm">
      <p className="font-medium text-ink">{title}</p>
      {hint && <p className="text-ink-soft">{hint}</p>}
      {action}
    </div>
  )
}
