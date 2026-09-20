export default function LoadingState({ label = 'Connecting to Thermion backend…' }) {
  return (
    <div className="flex items-center gap-2.5 py-8 text-sm text-ink-soft">
      <span
        className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-primary-200 border-t-primary-600"
        aria-hidden="true"
      />
      {label}
    </div>
  )
}
